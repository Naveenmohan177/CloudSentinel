def analyze_iscsi_evidence(host_evidence, container_evidence):
    findings = []

    modules = host_evidence.get("iscsi_modules", {}).get("stdout", "")
    configfs = host_evidence.get("configfs_mount", {}).get("stdout", "")
    iscsi_dir = host_evidence.get("iscsi_directory", {}).get("stdout", "")
    processes = host_evidence.get("iscsi_processes", {}).get("stdout", "")

    container_meta = (
        container_evidence
        .get("metadata", {})
        .get("stdout", "")
    )

    runtime = (
        container_evidence
        .get("runtime_configuration", {})
        .get("stdout", "")
    )

    # Host initiator/kernel evidence
    if "scsi_transport_iscsi" in modules:
        findings.append({
            "component": "iSCSI transport",
            "status": "HEALTHY",
            "evidence": "scsi_transport_iscsi kernel module is loaded",
        })
    else:
        findings.append({
            "component": "iSCSI transport",
            "status": "SUSPECTED",
            "evidence": "scsi_transport_iscsi module was not detected",
        })

    if configfs:
        findings.append({
            "component": "configfs",
            "status": "HEALTHY",
            "evidence": "configfs is mounted on the host",
        })
    else:
        findings.append({
            "component": "configfs",
            "status": "FAILED",
            "evidence": "configfs mount was not detected",
        })

    if "initiatorname.iscsi" in iscsi_dir:
        findings.append({
            "component": "iSCSI initiator configuration",
            "status": "HEALTHY",
            "evidence": "initiatorname.iscsi exists",
        })
    else:
        findings.append({
            "component": "iSCSI initiator configuration",
            "status": "SUSPECTED",
            "evidence": "initiatorname.iscsi was not found",
        })

    if "/sbin/iscsid" in processes:
        findings.append({
            "component": "host iscsid",
            "status": "RUNNING",
            "evidence": "host iscsid process exists",
        })

    # Container evidence
    if "|exited|1|" in container_meta:
        findings.append({
            "component": "Kolla iscsid container",
            "status": "FAILED",
            "evidence": "container exited with code 1",
        })

    # Runtime integration
    required_mounts = [
        "/sys/kernel/config",
        "/dev",
        "/run",
        "/lib/modules",
    ]

    missing = [
        mount for mount in required_mounts
        if mount not in runtime
    ]

    if not missing:
        findings.append({
            "component": "container host integration",
            "status": "HEALTHY",
            "evidence": "required host integration mounts are configured",
        })
    else:
        findings.append({
            "component": "container host integration",
            "status": "SUSPECTED",
            "evidence": "missing integration: " + ", ".join(missing),
        })

    return findings
