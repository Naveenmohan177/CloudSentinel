from datetime import datetime, timezone


def create_event(
    event_type,
    component,
    message,
    severity="INFO",
    details=None,
):
    return {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "event_type": event_type,
        "component": component,
        "severity": severity,
        "message": message,
        "details": details or {},
    }


def build_incident_timeline(report):
    events = []

    checks = report.get(
        "checks",
        {},
    )

    services = checks.get(
        "services",
        {},
    )

    events.append(
        create_event(
            "DETECTION",
            "systemd",
            "Infrastructure health checks completed.",
            (
                "CRITICAL"
                if services.get("status")
                == "CRITICAL"
                else "INFO"
            ),
            {
                "failed_services":
                    services.get(
                        "failed_services",
                        [],
                    ),
            },
        )
    )

    if report.get("diagnostics"):
        events.append(
            create_event(
                "DIAGNOSIS",
                "diagnostic-engine",
                "Failed service diagnostics collected.",
                "HIGH",
                {
                    "diagnostic_count":
                        len(
                            report[
                                "diagnostics"
                            ]
                        ),
                },
            )
        )

    rca = report.get("rca", {})

    if rca:
        events.append(
            create_event(
                "RCA",
                "CloudSentinel",
                rca.get(
                    "conclusion",
                    "Root cause candidates ranked.",
                ),
                "HIGH",
                {
                    "ranked_candidates":
                        rca.get(
                            "ranked_candidates",
                            [],
                        ),
                },
            )
        )

    storage = report.get(
        "openstack_storage_verification",
        {},
    )

    if storage:
        status = storage.get(
            "overall_status"
        )

        severity = (
            "HIGH"
            if status == "INCONSISTENT"
            else "WARNING"
            if status == "UNKNOWN"
            else "INFO"
        )

        events.append(
            create_event(
                "CONSISTENCY",
                "OpenStack Storage",
                (
                    "Cross-layer storage state evaluated."
                ),
                severity,
                {
                    "overall_status":
                        status,
                    "findings":
                        storage.get(
                            "findings",
                            [],
                        ),
                },
            )
        )

    if report.get("recovery_plan"):
        events.append(
            create_event(
                "POLICY",
                "Policy Engine",
                "Recovery actions classified by risk.",
                "INFO",
                {
                    "actions":
                        report[
                            "recovery_plan"
                        ],
                },
            )
        )

    if report.get("execution_results"):
        events.append(
            create_event(
                "EXECUTION",
                "Action Executor",
                "Recovery actions evaluated.",
                "INFO",
                {
                    "results":
                        report[
                            "execution_results"
                        ],
                },
            )
        )

    verification = report.get(
        "verification",
        {},
    )

    if verification:
        events.append(
            create_event(
                "VERIFICATION",
                "Verification Engine",
                "Post-recovery verification completed.",
                (
                    "CRITICAL"
                    if verification.get(
                        "overall_status"
                    ) == "FAILED"
                    else "INFO"
                ),
                verification,
            )
        )

    return events
