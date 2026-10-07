from dataclasses import dataclass


@dataclass
class Decision:
    incident_type: str
    conclusion: str
    confidence: str
    impact: str
    recommended_action: str
    reason: str
    risk: str
    verification_required: list
    status: str


def make_decision(report):
    rca = report.get("rca", {})
    candidates = rca.get("ranked_candidates", [])

    storage = report.get(
        "openstack_storage_verification",
        {}
    )

    storage_status = storage.get(
        "overall_status",
        "UNKNOWN"
    )

    findings = storage.get(
        "findings",
        []
    )

    verification = report.get(
        "verification",
        {}
    )

    verification_status = verification.get(
        "overall_status",
        "UNKNOWN"
    )

    top_candidate = (
        candidates[0]
        if candidates
        else {}
    )

    root_cause = top_candidate.get(
        "name",
        "Unknown root cause"
    )

    confidence = top_candidate.get(
        "status",
        "UNKNOWN"
    )

    if storage_status == "INCONSISTENT":

        classifications = [
            item.get("classification")
            for item in findings
        ]

        if "ISCSI_PATH_INCONSISTENCY" in classifications:

            return Decision(
                incident_type="STORAGE_PATH_FAILURE",
                conclusion=(
                    "The OpenStack control plane reports "
                    "a storage attachment, but the iSCSI "
                    "storage path is incomplete."
                ),
                confidence="HIGH",
                impact=(
                    "A VM may be unable to access an "
                    "attached Cinder volume."
                ),
                recommended_action=(
                    "Collect iSCSI, Cinder-volume and "
                    "Nova attachment diagnostics."
                ),
                reason=(
                    "Evidence collection is safer than "
                    "changing storage infrastructure."
                ),
                risk="SAFE",
                verification_required=[
                    "Cinder attachment state",
                    "Nova attachment state",
                    "libvirt disk presence",
                    "iSCSI session state",
                ],
                status="INVESTIGATE",
            )

        return Decision(
            incident_type="OPENSTACK_STATE_INCONSISTENCY",
            conclusion=(
                "OpenStack control-plane and infrastructure "
                "state disagree."
            ),
            confidence="HIGH",
            impact=(
                "The requested infrastructure operation "
                "may not have completed consistently."
            ),
            recommended_action=(
                "Collect evidence from the affected "
                "OpenStack and infrastructure layers."
            ),
            reason=(
                "Changing infrastructure before identifying "
                "the inconsistent layer could make recovery "
                "more difficult."
            ),
            risk="SAFE",
            verification_required=[
                "Cinder state",
                "Nova state",
                "libvirt state",
                "storage path state",
            ],
            status="INVESTIGATE",
        )

    if (
        verification_status == "FAILED"
        and storage_status == "CONSISTENT"
    ):

        return Decision(
            incident_type="SERVICE_FAILURE",
            conclusion=(
                f"The {root_cause} condition is isolated "
                "to the service layer; the current storage "
                "attachment state remains consistent."
            ),
            confidence=confidence,
            impact=(
                "Future Cinder volume attachment operations "
                "may be affected while the iSCSI service "
                "remains unhealthy."
            ),
            recommended_action=(
                "Collect service diagnostics and investigate "
                "the Kolla iscsid startup failure."
            ),
            reason=(
                "There is currently no storage attachment "
                "inconsistency requiring immediate recovery."
            ),
            risk="SAFE",
            verification_required=[
                "Kolla iscsid container running",
                "systemd service active",
                "host iscsid healthy",
                "iSCSI session available when attachment exists",
            ],
            status="INVESTIGATE",
        )

    return Decision(
        incident_type="UNKNOWN",
        conclusion=(
            "CloudSentinel does not have enough consistent "
            "evidence to recommend an infrastructure change."
        ),
        confidence="LOW",
        impact="Unknown.",
        recommended_action=(
            "Collect additional diagnostic evidence."
        ),
        reason=(
            "Infrastructure changes should not be performed "
            "without sufficient evidence."
        ),
        risk="SAFE",
        verification_required=[
            "Repeat health checks",
            "Validate OpenStack API state",
            "Validate infrastructure state",
        ],
        status="INVESTIGATE",
    )


def decision_to_dict(decision):
    return {
        "incident_type": decision.incident_type,
        "conclusion": decision.conclusion,
        "confidence": decision.confidence,
        "impact": decision.impact,
        "recommended_action": decision.recommended_action,
        "reason": decision.reason,
        "risk": decision.risk,
        "verification_required": (
            decision.verification_required
        ),
        "status": decision.status,
    }
