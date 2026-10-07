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


def collect_host_evidence():
    return {
        "kernel": run_command(
            ["uname", "-a"]
        ),

        "iscsi_modules": run_command(
            [
                "bash",
                "-c",
                "lsmod | grep -E 'iscsi|target|configfs' || true"
            ]
        ),

        "configfs_mount": run_command(
            [
                "bash",
                "-c",
                "mount | grep configfs || true"
            ]
        ),

        "configfs_target": run_command(
            [
                "bash",
                "-c",
                "ls -la /sys/kernel/config/target 2>&1 || true"
            ]
        ),

        "iscsi_directory": run_command(
            [
                "bash",
                "-c",
                "ls -la /etc/iscsi 2>&1 || true"
            ]
        ),

        "iscsi_processes": run_command(
            [
                "bash",
                "-c",
                "ps aux | grep -E '[i]scsid|[i]scsi' || true"
            ]
        ),

        "kernel_iscsi_module": run_command(
            [
                "bash",
                "-c",
                "modinfo iscsi_tcp 2>&1 || true"
            ]
        ),
    }


def collect_container_evidence(container_name):
    metadata = run_command(
        [
            "docker",
            "inspect",
            "--format",
            (
                "{{.Name}}|"
                "{{.Config.Image}}|"
                "{{.Config.Cmd}}|"
                "{{.HostConfig.NetworkMode}}|"
                "{{.HostConfig.Privileged}}|"
                "{{.State.Status}}|"
                "{{.State.ExitCode}}|"
                "{{.State.Error}}"
            ),
            container_name,
        ]
    )

    runtime_configuration = run_command(
        [
            "docker",
            "inspect",
            "--format",
            (
                "{{json .Mounts}}|"
                "{{json .HostConfig.Binds}}|"
                "{{json .HostConfig.CapAdd}}|"
                "{{json .HostConfig.SecurityOpt}}"
            ),
            container_name,
        ]
    )

    return {
        "container": container_name,
        "metadata": metadata,
        "runtime_configuration": runtime_configuration,
    }


def collect_kolla_iscsid_evidence():
    return {
        "container_logs": run_command(
            [
                "docker",
                "logs",
                "--tail",
                "100",
                "iscsid",
            ]
        ),

        "container_command": run_command(
            [
                "docker",
                "inspect",
                "--format",
                "{{json .Config.Cmd}}",
                "iscsid",
            ]
        ),

        "kolla_config_files": run_command(
            [
                "bash",
                "-c",
                "find /etc/kolla/iscsid -maxdepth 2 -type f "
                "-printf '%p\\n' 2>/dev/null | sort"
            ]
        ),

        "iscsid_systemd_unit": run_command(
            [
                "systemctl",
                "cat",
                "kolla-iscsid-container.service",
                "--no-pager",
            ]
        ),
    }
