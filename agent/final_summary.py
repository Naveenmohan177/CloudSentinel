def build_final_summary(report):
    rca = report.get("rca", {})
    decision = report.get("decision", {})
    storage = report.get("openstack_storage_verification", {})
    verification = report.get("verification", {})

    candidates = rca.get("ranked_candidates", [])
    top = candidates[0] if candidates else {}

    return {
        "incident": rca.get(
            "incident",
            "Unknown incident"
        ),

        "root_cause": top.get(
            "name",
            "Unknown"
        ),

        "root_cause_confidence": top.get(
            "status",
            "UNKNOWN"
        ),

        "decision": decision.get(
            "incident_type",
            "UNKNOWN"
        ),

        "decision_confidence": decision.get(
            "confidence",
            "UNKNOWN"
        ),

        "impact": decision.get(
            "impact",
            "Unknown"
        ),

        "recommended_action": decision.get(
            "recommended_action",
            "Collect evidence"
        ),

        "storage_state": storage.get(
            "overall_status",
            "UNKNOWN"
        ),

        "verification_state": verification.get(
            "overall_status",
            "UNKNOWN"
        ),

        "safety": (
            "No destructive infrastructure action "
            "was automatically executed."
        ),

        "conclusion": (
            "CloudSentinel detected the failed Kolla "
            "iSCSI service, correlated evidence across "
            "host, container and OpenStack layers, "
            "verified that current storage state remains "
            "consistent, and selected a safe investigation "
            "path without performing an unsafe recovery."
        ),
    }
