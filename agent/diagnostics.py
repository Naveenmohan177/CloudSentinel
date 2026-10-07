import subprocess


def run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
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


def diagnose_service(service_name):
    status = run_command(
        ["systemctl", "status", service_name, "--no-pager"]
    )

    failed_time = run_command(
        ["systemctl", "show", service_name, "-p", "ActiveState", "-p", "SubState"]
    )

    logs = run_command(
        ["journalctl", "-u", service_name, "-n", "30", "--no-pager"]
    )

    return {
        "service": service_name,
        "status": status,
        "state": failed_time,
        "recent_logs": logs,
    }


def diagnose_failed_services(failed_services):
    results = []

    for service_line in failed_services:
        parts = service_line.split()

        if len(parts) >= 4:
            service_name = parts[1]
            results.append(diagnose_service(service_name))

    return results
