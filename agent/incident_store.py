import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


REPORT_DIR = Path("reports")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_incident_id():
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    short_id = uuid.uuid4().hex[:8]

    return f"INC-{timestamp}-{short_id}"


def save_incident(report):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    incident_id = report.get("incident_id")

    if not incident_id:
        incident_id = create_incident_id()
        report["incident_id"] = incident_id

    report["created_at"] = report.get(
        "created_at",
        utc_now()
    )

    report.setdefault(
        "incident_status",
        "OPEN"
    )

    report.setdefault(
        "severity",
        "HIGH"
    )

    report.setdefault(
        "affected_components",
        []
    )

    report.setdefault(
        "timeline",
        []
    )

    path = REPORT_DIR / f"{incident_id}.json"

    with path.open("w") as f:
        json.dump(
            report,
            f,
            indent=2
        )

    return str(path)


def list_incidents():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    return sorted(
        REPORT_DIR.glob("INC-*.json")
    )


def load_incident(path):
    with Path(path).open() as f:
        return json.load(f)
