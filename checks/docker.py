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

    except Exception as exc:
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def inspect_container(container_name):
    status = run_command(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}|{{.State.ExitCode}}|{{.State.Error}}",
            container_name,
        ]
    )

    logs = run_command(
        [
            "docker",
            "logs",
            "--tail",
            "50",
            container_name,
        ]
    )

    return {
        "container": container_name,
        "status": status,
        "logs": logs,
    }


def check_container(container_name):
    result = inspect_container(container_name)

    status_output = result["status"]["stdout"]

    if status_output:
        parts = status_output.split("|", 2)

        state = parts[0]
        exit_code = parts[1]
        error = parts[2] if len(parts) > 2 else ""

        return {
            "container": container_name,
            "state": state,
            "exit_code": exit_code,
            "docker_error": error,
            "logs": result["logs"]["stdout"],
        }

    return {
        "container": container_name,
        "state": "UNKNOWN",
        "exit_code": None,
        "docker_error": result["status"]["stderr"],
        "logs": result["logs"]["stdout"],
    }
