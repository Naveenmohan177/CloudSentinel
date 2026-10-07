import json

from checks.linux import run_linux_health_checks
from checks.docker import check_container

from agent.diagnostics import diagnose_failed_services

from agent.evidence import (
    collect_host_evidence,
    collect_container_evidence,
    collect_kolla_iscsid_evidence,
)

from agent.rca import build_rca
from agent.rca_scoring import score_iscsi_root_causes

from agent.recovery import generate_recovery_plan
from agent.executor import execute_action
from agent.verification import verify_iscsid_recovery

from agent.openstack_verify import verify_openstack_storage

from agent.dependency import calculate_affected_components

from agent.events import build_incident_timeline

from agent.decision import (
    make_decision,
    decision_to_dict,
)

from agent.incident_store import save_incident
from agent.final_summary import build_final_summary


# ============================================================
# CLOUDSENTINEL LAB CONFIGURATION
# ============================================================

VOLUME_ID = "8db1deca-cec2-4ee8-9cbe-f1ecabc4dfd1"

SERVER_ID = "63b58d44-bea2-402c-9e4f-cf3cd92b65b0"

LIBVIRT_DOMAIN = "instance-00000005"


# ============================================================
# RCA CONCLUSION
# ============================================================

def build_rca_conclusion(candidates):

    if not candidates:
        return "No root-cause candidates were generated."

    top = candidates[0]

    name = top.get(
        "name",
        "Unknown root cause"
    )

    status = top.get(
        "status",
        "UNKNOWN"
    )

    if status == "CONFIRMED":
        return f"Root cause confirmed: {name}."

    if status == "PROBABLE":
        return f"Most probable root cause: {name}."

    if status == "POSSIBLE":
        return (
            f"Possible root cause requiring further "
            f"investigation: {name}."
        )

    return (
        f"No strong root-cause candidate was identified. "
        f"Top candidate: {name}."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # DETECTION
    # --------------------------------------------------------

    health = run_linux_health_checks()

    report = {
        "component": "CloudSentinel",
        "host": "local",

        "checks": health,

        "diagnostics": [],
        "container_diagnostics": [],

        "evidence": {},

        "rca": {},

        "openstack_storage_verification": {},

        "affected_components": [],

        "decision": {},

        "recovery_plan": [],

        "execution_results": [],

        "verification": {},

        "timeline": [],

        "incident_status": "OPEN",

        "severity": "HIGH",
    }

    failed_services = (
        health
        .get("services", {})
        .get("failed_services", [])
    )

    # --------------------------------------------------------
    # DIAGNOSIS
    # --------------------------------------------------------

    if failed_services:

        report["diagnostics"] = (
            diagnose_failed_services(
                failed_services
            )
        )

    # --------------------------------------------------------
    # ISCSID EVIDENCE
    # --------------------------------------------------------

    iscsid_failure = any(
        "kolla-iscsid-container.service" in service
        for service in failed_services
    )

    if iscsid_failure:

        report["container_diagnostics"].append(
            check_container("iscsid")
        )

        report["evidence"]["host"] = (
            collect_host_evidence()
        )

        report["evidence"]["container"] = (
            collect_container_evidence(
                "iscsid"
            )
        )

        report["evidence"]["kolla_iscsid"] = (
            collect_kolla_iscsid_evidence()
        )

    # --------------------------------------------------------
    # RCA
    # --------------------------------------------------------

    if report["evidence"]:

        report["rca"] = build_rca(
            report
        )

        candidates = (
            score_iscsi_root_causes(
                report
            )
        )

        report["rca"]["ranked_candidates"] = (
            candidates
        )

        report["rca"]["conclusion"] = (
            build_rca_conclusion(
                candidates
            )
        )

    # --------------------------------------------------------
    # OPENSTACK CROSS-LAYER VERIFICATION
    # --------------------------------------------------------

    try:

        storage = verify_openstack_storage(
            volume_id=VOLUME_ID,
            server_id=SERVER_ID,
            domain=LIBVIRT_DOMAIN,
        )

        report[
            "openstack_storage_verification"
        ] = storage

    except Exception as exc:

        report[
            "openstack_storage_verification"
        ] = {
            "overall_status": "UNKNOWN",

            "findings": [
                {
                    "severity": "WARNING",

                    "classification":
                        "VERIFICATION_ERROR",

                    "message":
                        "OpenStack storage verification "
                        "could not be completed.",
                }
            ],

            "error": str(exc),
        }

    # --------------------------------------------------------
    # AFFECTED COMPONENTS
    # --------------------------------------------------------

    storage_findings = (
        report[
            "openstack_storage_verification"
        ].get(
            "findings",
            []
        )
    )

    incident_components = []

    if iscsid_failure:

        incident_components.extend([
            "iscsid",
            "cinder-volume",
            "cinder",
        ])

    report["affected_components"] = (
        calculate_affected_components(
            storage_findings,
            incident_components,
        )
    )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    report["verification"] = (
        verify_iscsid_recovery()
    )

    # --------------------------------------------------------
    # DECISION ENGINE
    # --------------------------------------------------------

    decision = make_decision(
        report
    )

    report["decision"] = (
        decision_to_dict(
            decision
        )
    )

    # --------------------------------------------------------
    # RECOVERY POLICY
    # --------------------------------------------------------

    if report["rca"]:

        incident = report[
            "rca"
        ].get(
            "incident",
            "unknown incident"
        )

        report["recovery_plan"] = (
            generate_recovery_plan(
                incident
            )
        )

        for action in report[
            "recovery_plan"
        ]:

            report[
                "execution_results"
            ].append(
                execute_action(
                    action,
                    dry_run=True
                )
            )

    # --------------------------------------------------------
    # FINAL INCIDENT STATE
    # --------------------------------------------------------

    storage_status = (
        report[
            "openstack_storage_verification"
        ].get(
            "overall_status"
        )
    )

    verification_status = (
        report[
            "verification"
        ].get(
            "overall_status"
        )
    )

    if (
        storage_status == "INCONSISTENT"
        or verification_status == "FAILED"
    ):

        report["incident_status"] = "OPEN"
        report["severity"] = "HIGH"

    elif storage_status == "UNKNOWN":

        report["incident_status"] = "OPEN"
        report["severity"] = "MEDIUM"

    else:

        report["incident_status"] = "RESOLVED"
        report["severity"] = "INFO"

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    report["timeline"] = (
        build_incident_timeline(
            report
        )
    )

    # --------------------------------------------------------
    # FINAL INTELLIGENCE
    # --------------------------------------------------------

    report["final_summary"] = build_final_summary(
        report
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    report_path = save_incident(
        report
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print("========================================")
    print("       CLOUDSENTINEL INCIDENT")
    print("========================================")

    # --------------------------------------------------------
    # RCA
    # --------------------------------------------------------

    print("\n[1] RCA")

    rca = report.get(
        "rca",
        {}
    )

    if rca:

        print(
            f"Incident: "
            f"{rca.get('incident')}"
        )

        print(
            f"Conclusion: "
            f"{rca.get('conclusion')}"
        )

        for candidate in rca.get(
            "ranked_candidates",
            []
        ):

            print(
                f"  [{candidate.get('status')}] "
                f"{candidate.get('name')} "
                f"(score={candidate.get('score')})"
            )

            for evidence in candidate.get(
                "evidence",
                []
            ):

                print(
                    f"      └─ {evidence}"
                )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    print("\n[2] INCIDENT DECISION")

    decision = report.get(
        "decision",
        {}
    )

    print(
        f"  Type: "
        f"{decision.get('incident_type')}"
    )

    print(
        f"  Confidence: "
        f"{decision.get('confidence')}"
    )

    print(
        f"  Status: "
        f"{decision.get('status')}"
    )

    print(
        f"  Conclusion: "
        f"{decision.get('conclusion')}"
    )

    print(
        f"  Impact: "
        f"{decision.get('impact')}"
    )

    print(
        f"  Recommended action: "
        f"{decision.get('recommended_action')}"
    )

    print(
        f"  Risk: "
        f"{decision.get('risk')}"
    )

    # --------------------------------------------------------
    # STORAGE
    # --------------------------------------------------------

    print("\n[3] OPENSTACK STORAGE")

    storage = report[
        "openstack_storage_verification"
    ]

    print(
        f"  Overall: "
        f"{storage.get('overall_status')}"
    )

    for finding in storage.get(
        "findings",
        []
    ):

        print(
            f"  [{finding.get('severity')}] "
            f"{finding.get('classification')}"
        )

        print(
            f"      └─ "
            f"{finding.get('message')}"
        )

    # --------------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------------

    print("\n[4] AFFECTED COMPONENTS")

    if report["affected_components"]:

        for component in report[
            "affected_components"
        ]:

            print(
                f"  → {component}"
            )

    else:

        print(
            "  → None identified"
        )

    # --------------------------------------------------------
    # RECOVERY
    # --------------------------------------------------------

    print("\n[5] RECOVERY PLAN")

    for action in report[
        "recovery_plan"
    ]:

        print(
            f"  [{action.get('risk')}] "
            f"{action.get('action')}"
        )

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    print("\n[6] EXECUTION")

    for result in report[
        "execution_results"
    ]:

        print(
            f"  [{result.get('status')}] "
            f"{result.get('action')}"
        )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    print("\n[7] VERIFICATION")

    print(
        f"  Overall: "
        f"{report['verification'].get('overall_status')}"
    )

    for check in report[
        "verification"
    ].get(
        "checks",
        []
    ):

        print(
            f"  [{check.get('status')}] "
            f"{check.get('check')}"
        )

        evidence = check.get(
            "evidence"
        )

        if evidence:

            print(
                f"      └─ {evidence}"
            )

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    print("\n[8] INCIDENT TIMELINE")

    for event in report[
        "timeline"
    ]:

        print(
            f"  [{event.get('event_type')}] "
            f"{event.get('component')} "
            f"→ {event.get('message')}"
        )

    # --------------------------------------------------------
    # FINAL STATE
    # --------------------------------------------------------

    print()

    print(
        f"Incident ID: "
        f"{report.get('incident_id')}"
    )

    print(
        f"Status: "
        f"{report.get('incident_status')}"
    )

    print(
        f"Severity: "
        f"{report.get('severity')}"
    )

    print()

    print(
        f"Incident report saved to: "
        f"{report_path}"
    )

    print("\n[9] FINAL INTELLIGENCE")

    summary = report.get(
        "final_summary",
        {}
    )

    print(
        f"  Root cause: "
        f"{summary.get('root_cause')}"
    )

    print(
        f"  Confidence: "
        f"{summary.get('root_cause_confidence')}"
    )

    print(
        f"  Decision: "
        f"{summary.get('decision')}"
    )

    print(
        f"  Storage: "
        f"{summary.get('storage_state')}"
    )

    print(
        f"  Verification: "
        f"{summary.get('verification_state')}"
    )

    print(
        f"  Safety: "
        f"{summary.get('safety')}"
    )

    print(
        f"  Conclusion: "
        f"{summary.get('conclusion')}"
    )

    print()
    print("========================================")


if __name__ == "__main__":
    main()
