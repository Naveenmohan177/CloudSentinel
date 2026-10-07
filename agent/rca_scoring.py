def _candidate(name, score, status, evidence):
    return {
        "name": name,
        "score": score,
        "status": status,
        "evidence": evidence,
    }


def score_iscsi_root_causes(report):
    scores = []

    host = report.get("evidence", {}).get("host", {})
    container = report.get("evidence", {}).get("container", {})
    kolla = report.get("evidence", {}).get("kolla_iscsid", {})

    modules = host.get("iscsi_modules", {}).get("stdout", "")
    configfs = host.get("configfs_mount", {}).get("stdout", "")
    iscsi_dir = host.get("iscsi_directory", {}).get("stdout", "")
    processes = host.get("iscsi_processes", {}).get("stdout", "")

    metadata = container.get("metadata", {}).get("stdout", "")
    runtime = container.get("runtime_configuration", {}).get("stdout", "")
    logs = kolla.get("container_logs", {}).get("stdout", "")

    # ---------------------------------------------------------
    # 1. Kolla iscsid container startup
    # ---------------------------------------------------------

    evidence = []
    score = 0

    if "|exited|1|" in metadata:
        score += 50
        evidence.append(
            "Kolla iscsid container exited with code 1."
        )

    if "kolla_start" in logs:
        score += 10
        evidence.append(
            "Container logs show Kolla startup processing."
        )

    if "host" in metadata:
        score += 5
        evidence.append(
            "Container uses host networking."
        )

    if runtime:
        score += 5
        evidence.append(
            "Container runtime configuration is available."
        )

    status = (
        "CONFIRMED" if score >= 70
        else "PROBABLE" if score >= 40
        else "POSSIBLE" if score > 0
        else "RULED_OUT"
    )

    scores.append(
        _candidate(
            "Kolla iscsid container startup failure",
            score,
            status,
            evidence,
        )
    )

    # ---------------------------------------------------------
    # 2. Host iSCSI kernel support
    # ---------------------------------------------------------

    evidence = []
    score = 0

    if "scsi_transport_iscsi" in modules:
        evidence.append(
            "iSCSI transport module is loaded."
        )
    else:
        score = 80
        evidence.append(
            "iSCSI transport module is missing."
        )

    status = (
        "PROBABLE" if score >= 70
        else "POSSIBLE" if score > 0
        else "RULED_OUT"
    )

    scores.append(
        _candidate(
            "Missing host iSCSI kernel support",
            score,
            status,
            evidence,
        )
    )

    # ---------------------------------------------------------
    # 3. configfs
    # ---------------------------------------------------------

    evidence = []
    score = 0

    if "configfs on /sys/kernel/config" in configfs:
        evidence.append(
            "configfs is mounted on the host."
        )
    else:
        score = 80
        evidence.append(
            "configfs is not mounted."
        )

    status = (
        "PROBABLE" if score >= 70
        else "POSSIBLE" if score > 0
        else "RULED_OUT"
    )

    scores.append(
        _candidate(
            "Missing configfs support",
            score,
            status,
            evidence,
        )
    )

    # ---------------------------------------------------------
    # 4. iSCSI initiator configuration
    # ---------------------------------------------------------

    evidence = []
    score = 0

    if "initiatorname.iscsi" in iscsi_dir:
        evidence.append(
            "iSCSI initiator configuration exists."
        )
    else:
        score = 70
        evidence.append(
            "initiatorname.iscsi was not found."
        )

    status = (
        "PROBABLE" if score >= 70
        else "POSSIBLE" if score > 0
        else "RULED_OUT"
    )

    scores.append(
        _candidate(
            "Missing iSCSI initiator configuration",
            score,
            status,
            evidence,
        )
    )

    # ---------------------------------------------------------
    # 5. Host iscsid
    # ---------------------------------------------------------

    evidence = []
    score = 0

    if "iscsid" in processes:
        evidence.append(
            "Host iscsid process is running."
        )
    else:
        score = 75
        evidence.append(
            "Host iscsid process is not running."
        )

    status = (
        "PROBABLE" if score >= 70
        else "POSSIBLE" if score > 0
        else "RULED_OUT"
    )

    scores.append(
        _candidate(
            "Host iscsid failure",
            score,
            status,
            evidence,
        )
    )

    scores.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scores
