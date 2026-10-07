import subprocess


def execute_action(action, dry_run=True):
    risk = action.get("risk", "BLOCKED")
    command = action.get("command", [])

    result = {
        "action": action.get("action"),
        "risk": risk,
        "command": command,
        "executed": False,
        "return_code": None,
        "stdout": "",
        "stderr": "",
    }

    # Safety boundary
    if risk != "SAFE":
        result["status"] = "REFUSED"
        result["reason"] = (
            "Action is not SAFE. Human approval is required "
            "or the operation is blocked."
        )
        return result

    if dry_run:
        result["status"] = "DRY_RUN"
        result["reason"] = "Execution disabled in dry-run mode."
        return result

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        result["executed"] = True
        result["return_code"] = completed.returncode
        result["stdout"] = completed.stdout.strip()
        result["stderr"] = completed.stderr.strip()

        if completed.returncode == 0:
            result["status"] = "SUCCESS"
        else:
            result["status"] = "FAILED"

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["reason"] = "Command exceeded the 30-second timeout."

    except Exception as exc:
        result["status"] = "ERROR"
        result["reason"] = str(exc)

    return result
