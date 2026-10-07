import os
import shutil
import subprocess


def get_status(usage, warning, critical):
    if usage >= critical:
        return "CRITICAL"
    elif usage >= warning:
        return "WARNING"
    return "OK"


def check_cpu():
    load1, load5, load15 = os.getloadavg()

    cpu_count = os.cpu_count() or 1
    load_percent = (load1 / cpu_count) * 100

    return {
        "check": "cpu_load",
        "status": get_status(load_percent, 80, 100),
        "cpu_count": cpu_count,
        "load_1m": round(load1, 2),
        "load_5m": round(load5, 2),
        "load_15m": round(load15, 2),
        "load_percent_estimate": round(load_percent, 2),
    }


def check_memory():
    result = subprocess.run(
        ["free", "-m"],
        capture_output=True,
        text=True,
        check=True
    )

    for line in result.stdout.splitlines():
        if line.startswith("Mem:"):
            parts = line.split()

            total = int(parts[1])
            used = int(parts[2])
            available = int(parts[6])

            usage = (used / total) * 100

            return {
                "check": "memory",
                "status": get_status(usage, 80, 90),
                "total_mb": total,
                "used_mb": used,
                "available_mb": available,
                "usage_percent": round(usage, 2),
            }


def check_disk():
    total, used, free = shutil.disk_usage("/")

    usage = (used / total) * 100

    return {
        "check": "root_disk",
        "status": get_status(usage, 85, 95),
        "total_gb": round(total / (1024 ** 3), 2),
        "used_gb": round(used / (1024 ** 3), 2),
        "free_gb": round(free / (1024 ** 3), 2),
        "usage_percent": round(usage, 2),
    }


def check_failed_services():
    result = subprocess.run(
        ["systemctl", "--failed", "--no-legend", "--no-pager"],
        capture_output=True,
        text=True
    )

    failed = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    return {
        "check": "systemd_services",
        "status": "OK" if not failed else "CRITICAL",
        "failed_count": len(failed),
        "failed_services": failed,
    }


def run_linux_health_checks():
    return {
        "cpu": check_cpu(),
        "memory": check_memory(),
        "disk": check_disk(),
        "services": check_failed_services(),
    }
