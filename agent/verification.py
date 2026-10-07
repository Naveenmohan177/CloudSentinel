import subprocess


def run_command(command, timeout=10):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": "Command timed out",
        }

    except Exception as exc:
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def verify_iscsid():
    result = run_command(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}|{{.State.ExitCode}}",
            "iscsid",
        ]
    )

    output = result["stdout"]

    if result["return_code"] != 0:
        return {
            "check": "iscsid_container",
            "status": "UNKNOWN",
            "evidence": result["stderr"],
        }

    parts = output.split("|")

    state = parts[0]
    exit_code = parts[1] if len(parts) > 1 else ""

    if state == "running":
        return {
            "check": "iscsid_container",
            "status": "HEALTHY",
            "evidence": f"Container state={state}, exit_code={exit_code}",
        }

    return {
        "check": "iscsid_container",
        "status": "FAILED",
        "evidence": f"Container state={state}, exit_code={exit_code}",
    }


def verify_host_iscsid():
    result = run_command(
        [
            "pgrep",
            "-x",
            "iscsid",
        ]
    )

    if result["return_code"] == 0:
        return {
            "check": "host_iscsid",
            "status": "HEALTHY",
            "evidence": "Host iscsid process is running.",
        }

    return {
        "check": "host_iscsid",
        "status": "FAILED",
        "evidence": "Host iscsid process was not detected.",
    }


def verify_systemd_service():
    result = run_command(
        [
            "systemctl",
            "is-active",
            "kolla-iscsid-container.service",
        ]
    )

    if result["stdout"] == "active":
        return {
            "check": "kolla_iscsid_systemd",
            "status": "HEALTHY",
            "evidence": "Systemd reports the service as active.",
        }

    return {
        "check": "kolla_iscsid_systemd",
        "status": "FAILED",
        "evidence": (
            "Systemd reports: "
            + (result["stdout"] or result["stderr"])
        ),
    }


def verify_iscsid_recovery():
    checks = [
        verify_iscsid(),
        verify_host_iscsid(),
        verify_systemd_service(),
    ]

    failed = [
        check for check in checks
        if check["status"] == "FAILED"
    ]

    if failed:
        overall = "FAILED"
    elif any(check["status"] == "UNKNOWN" for check in checks):
        overall = "UNKNOWN"
    else:
        overall = "HEALTHY"

    return {
        "overall_status": overall,
        "checks": checks,
    }


def verify_iscsi_sessions(expected_session=False):
    result = run_command(
        [
            "bash",
            "-c",
            "iscsiadm -m session 2>&1 || true",
        ]
    )

    output = result["stdout"]

    if "No active sessions" in output or not output:
        if expected_session:
            return {
                "check": "iscsi_sessions",
                "status": "FAILED",
                "evidence": "Expected an iSCSI session, but none was detected.",
            }

        return {
            "check": "iscsi_sessions",
            "status": "NOT_APPLICABLE",
            "evidence": "No active iSCSI session is currently expected.",
        }

    return {
        "check": "iscsi_sessions",
        "status": "HEALTHY",
        "evidence": output,
    }
