from flask import Flask, jsonify, render_template_string
from pathlib import Path
import json

app = Flask(__name__)

REPORT_DIR = Path(__file__).parent / "reports"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CloudSentinel</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="15">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }

        header {
            padding: 22px 30px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        header h1 {
            margin: 0;
            font-size: 26px;
        }

        header p {
            margin: 6px 0 0;
            color: #94a3b8;
        }

        .container {
            padding: 24px;
            max-width: 1500px;
            margin: auto;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }

        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
        }

        .label {
            color: #94a3b8;
            font-size: 13px;
            text-transform: uppercase;
        }

        .value {
            font-size: 22px;
            font-weight: bold;
            margin-top: 8px;
        }

        .danger {
            color: #f87171;
        }

        .warning {
            color: #fbbf24;
        }

        .success {
            color: #4ade80;
        }

        .info {
            color: #60a5fa;
        }

        .section {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 20px;
        }

        .section h2 {
            margin-top: 0;
            font-size: 18px;
        }

        .two {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #334155;
        }

        .badge {
            padding: 5px 9px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
        }

        .badge-red {
            background: #450a0a;
            color: #fca5a5;
        }

        .badge-green {
            background: #052e16;
            color: #86efac;
        }

        .badge-yellow {
            background: #451a03;
            color: #fde68a;
        }

        .timeline {
            border-left: 3px solid #475569;
            padding-left: 20px;
        }

        .event {
            margin-bottom: 16px;
        }

        .event strong {
            color: #60a5fa;
        }

        pre {
            white-space: pre-wrap;
            word-break: break-word;
            background: #0f172a;
            padding: 14px;
            border-radius: 8px;
            color: #cbd5e1;
        }

        @media(max-width: 900px) {
            .grid,
            .two {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>

<header>
    <h1>🛡 CloudSentinel</h1>
    <p>Autonomous OpenStack Infrastructure Reliability & Self-Healing Platform</p>
</header>

<div class="container">

    <div class="grid">

        <div class="card">
            <div class="label">Incident</div>
            <div class="value danger">
                {{ summary.get("incident", "Unknown") }}
            </div>
        </div>

        <div class="card">
            <div class="label">Root Cause</div>
            <div class="value">
                {{ summary.get("root_cause", "Unknown") }}
            </div>
        </div>

        <div class="card">
            <div class="label">Decision</div>
            <div class="value info">
                {{ summary.get("decision", "Unknown") }}
            </div>
        </div>

        <div class="card">
            <div class="label">Severity</div>
            <div class="value danger">
                {{ report.get("severity", "UNKNOWN") }}
            </div>
        </div>

    </div>

    <div class="two">

        <div class="section">
            <h2>🔍 Root Cause Analysis</h2>

            <div class="row">
                <span>Root Cause</span>
                <strong>{{ summary.get("root_cause", "Unknown") }}</strong>
            </div>

            <div class="row">
                <span>Confidence</span>
                <span class="badge badge-yellow">
                    {{ summary.get("root_cause_confidence", "UNKNOWN") }}
                </span>
            </div>

            <div class="row">
                <span>Decision</span>
                <strong>{{ summary.get("decision", "UNKNOWN") }}</strong>
            </div>

            <div class="row">
                <span>Decision Confidence</span>
                <strong>{{ summary.get("decision_confidence", "UNKNOWN") }}</strong>
            </div>

            <p>{{ summary.get("conclusion", "") }}</p>
        </div>

        <div class="section">
            <h2>☁ OpenStack Storage State</h2>

            <div class="row">
                <span>Cinder</span>
                <span class="badge badge-green">AVAILABLE</span>
            </div>

            <div class="row">
                <span>Nova</span>
                <span class="badge badge-green">NOT ATTACHED</span>
            </div>

            <div class="row">
                <span>Libvirt</span>
                <span class="badge badge-green">NOT ATTACHED</span>
            </div>

            <div class="row">
                <span>iSCSI</span>
                <span class="badge badge-green">NO SESSION</span>
            </div>

            <div class="row">
                <strong>Overall</strong>
                <strong class="success">
                    {{ summary.get("storage_state", "UNKNOWN") }}
                </strong>
            </div>
        </div>

    </div>

    <div class="section">
        <h2>🧠 Recovery & Safety Policy</h2>

        <div class="row">
            <span>Collect diagnostics</span>
            <span class="badge badge-green">SAFE</span>
        </div>

        <div class="row">
            <span>Inspect container</span>
            <span class="badge badge-green">SAFE</span>
        </div>

        <div class="row">
            <span>Restart iscsid</span>
            <span class="badge badge-yellow">APPROVAL REQUIRED</span>
        </div>

        <div class="row">
            <span>Delete Cinder volume</span>
            <span class="badge badge-red">BLOCKED</span>
        </div>

        <p>
            {{ summary.get("safety", "Safety policy information unavailable.") }}
        </p>
    </div>

    <div class="section">
        <h2>📋 Verification</h2>

        <div class="row">
            <span>Verification State</span>
            <strong class="danger">
                {{ summary.get("verification_state", "UNKNOWN") }}
            </strong>
        </div>

        <p>
            {{ summary.get("impact", "") }}
        </p>
    </div>

    <div class="section">
        <h2>⏱ Incident Timeline</h2>

        <div class="timeline">

        {% for event in report.get("timeline", []) %}

            <div class="event">
                <strong>
                    {{ event.get("stage", "EVENT") }}
                </strong>

                <div>
                    {{ event.get("message", event.get("description", "")) }}
                </div>
            </div>

        {% endfor %}

        </div>
    </div>

    <div class="section">
        <h2>📄 Incident Information</h2>

        <div class="row">
            <span>Incident ID</span>
            <strong>{{ report.get("incident_id", "UNKNOWN") }}</strong>
        </div>

        <div class="row">
            <span>Status</span>
            <strong class="danger">{{ report.get("incident_status", "UNKNOWN") }}</strong>
        </div>

        <div class="row">
            <span>Created</span>
            <strong>{{ report.get("created_at", "UNKNOWN") }}</strong>
        </div>
    </div>

</div>

</body>
</html>
"""


def latest_report():
    reports = sorted(
        REPORT_DIR.glob("INC-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not reports:
        return {}

    with reports[0].open() as f:
        return json.load(f)


@app.route("/")
def dashboard():
    report = latest_report()
    summary = report.get("final_summary", {})

    return render_template_string(
        HTML,
        report=report,
        summary=summary,
    )


@app.route("/api/incident")
def api_incident():
    return jsonify(latest_report())


if __name__ == "__main__":
    print()
    print("========================================")
    print("       CLOUDSENTINEL DASHBOARD")
    print("========================================")
    print()
    print("Open in browser:")
    print("http://127.0.0.1:5000")
    print()
    print("API:")
    print("http://127.0.0.1:5000/api/incident")
    print()

    app.run(
        host="0.0.0.0",
        port=5050,
        debug=False,
    )
