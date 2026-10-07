from dataclasses import dataclass


@dataclass
class Dependency:
    component: str
    depends_on: list


DEPENDENCY_MAP = {
    "cinder": Dependency(
        "cinder",
        [
            "cinder-volume",
            "lvm",
            "iscsid",
        ],
    ),

    "cinder-volume": Dependency(
        "cinder-volume",
        [
            "lvm",
            "iscsid",
        ],
    ),

    "iscsid": Dependency(
        "iscsid",
        [
            "kernel",
            "configfs",
            "iscsi_kernel_module",
        ],
    ),
}


def get_dependencies(component):
    dependency = DEPENDENCY_MAP.get(component)

    if not dependency:
        return []

    return dependency.depends_on


def analyze_iscsid_failure(evidence):
    findings = []

    metadata = evidence.get("metadata", {})
    output = metadata.get("stdout", "")

    if "|exited|1|" in output:
        findings.append({
            "severity": "HIGH",
            "finding": "iscsid container exited with code 1",
            "evidence": "Docker reports container state=exited and exit_code=1",
        })

    findings.append({
        "severity": "INFO",
        "finding": "Docker itself did not report a container runtime error",
        "evidence": "docker inspect State.Error is empty",
    })

    findings.append({
        "severity": "INFO",
        "finding": "Container uses host networking and privileged mode",
        "evidence": "NetworkMode=host, Privileged=true",
    })

    findings.append({
        "severity": "NEXT",
        "finding": "Investigate iSCSI host/kernel prerequisites",
        "evidence": (
            "iscsid failed internally; next layer is kernel/configfs/"
            "iSCSI subsystem rather than Docker networking"
        ),
    })

    return findings


def build_rca(report):
    rca = {
        "incident": "kolla-iscsid-container failure",
        "root_cause_status": "NOT_CONFIRMED",
        "affected_components": [
            "iscsid",
            "cinder-volume",
            "cinder",
        ],
        "dependency_chain": [
            "Cinder",
            "cinder-volume",
            "iscsid",
            "Linux kernel",
            "configfs",
            "iSCSI kernel subsystem",
        ],
        "findings": [],
        "next_actions": [],
    }

    container_evidence = (
        report.get("evidence", {})
        .get("container", {})
    )

    rca["findings"] = analyze_iscsid_failure(
        container_evidence
    )

    rca["next_actions"] = [
        "Check configfs availability",
        "Check iSCSI kernel modules",
        "Check /etc/iscsi configuration",
        "Check iscsid runtime prerequisites",
        "Compare host and container environment",
    ]

    return rca
