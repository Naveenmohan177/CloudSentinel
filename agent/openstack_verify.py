import json
import os
import shutil
import subprocess


OPENSTACK_CLI = os.environ.get(
    "CLOUDSENTINEL_OPENSTACK_CLI",
    shutil.which("openstack") or "openstack",
)


def run_command(command, timeout=15):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": "Command timed out",
        }

    except Exception as exc:
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def openstack_json(args):
    result = run_command(
        [OPENSTACK_CLI] + args + ["-f", "json"]
    )

    if result["return_code"] != 0:
        return {
            "status": "UNKNOWN",
            "error": result["stderr"],
        }

    try:
        return {
            "status": "HEALTHY",
            "data": json.loads(result["stdout"]),
        }

    except json.JSONDecodeError as exc:
        return {
            "status": "UNKNOWN",
            "error": f"Invalid JSON from OpenStack CLI: {exc}",
        }


def verify_cinder_volume(volume_id):
    result = openstack_json(
        ["volume", "show", volume_id]
    )

    if result["status"] != "HEALTHY":
        return {
            "check": "cinder_volume",
            "status": "UNKNOWN",
            "reason": result["error"],
        }

    data = result["data"]

    attachments = data.get(
        "attachments",
        []
    )

    return {
        "check": "cinder_volume",
        "status": "HEALTHY",
        "volume_status": data.get("status"),
        "attachments": attachments,
        "attachment_count": len(attachments),
        "evidence": data,
    }


def verify_nova_attachment(server_id, volume_id):
    result = openstack_json(
        ["server", "show", server_id]
    )

    if result["status"] != "HEALTHY":
        return {
            "check": "nova_attachment",
            "status": "UNKNOWN",
            "volume_id": volume_id,
            "reason": result["error"],
        }

    data = result["data"]

    attached_volumes = data.get(
        "volumes_attached",
        []
    )

    attached_ids = []

    for item in attached_volumes:

        if isinstance(item, dict):

            volume_id_value = item.get(
                "id"
            )

            if volume_id_value:
                attached_ids.append(
                    volume_id_value
                )

    attached = volume_id in attached_ids

    return {
        "check": "nova_attachment",
        "status": (
            "ATTACHED"
            if attached
            else "NOT_ATTACHED"
        ),
        "volume_id": volume_id,
        "attached_volume_ids": attached_ids,
        "evidence": data,
    }


def verify_libvirt_disk(
    domain,
    device="vdb",
):
    """
    Verify the hypervisor-level disk using virsh.

    Preferred path:
        host virsh

    Fallback:
        Kolla nova_libvirt container
    """

    host_virsh = shutil.which("virsh")

    if host_virsh:

        command = [
            host_virsh,
            "domblklist",
            domain,
            "--details",
        ]

        source = "host"

    else:

        command = [
            "docker",
            "exec",
            "nova_libvirt",
            "virsh",
            "domblklist",
            domain,
            "--details",
        ]

        source = "nova_libvirt"

    result = run_command(command)

    if result["return_code"] != 0:

        return {
            "check": "libvirt_disk",
            "status": "UNKNOWN",
            "reason": "libvirt query failed.",
            "source": source,
            "evidence": (
                result["stderr"]
                or result["stdout"]
            ),
        }

    output = result["stdout"]

    found = False

    for line in output.splitlines():

        fields = line.split()

        if device in fields:
            found = True
            break

    return {
        "check": "libvirt_disk",
        "status": (
            "ATTACHED"
            if found
            else "NOT_ATTACHED"
        ),
        "device": device,
        "domain": domain,
        "source": source,
        "evidence": output,
    }


def verify_iscsi_session(expected=False):
    result = run_command(
        [
            "bash",
            "-c",
            "iscsiadm -m session 2>&1 || true",
        ]
    )

    output = result["stdout"]

    if (
        not output
        or "No active sessions" in output
    ):

        if expected:

            return {
                "check": "iscsi_session",
                "status": "FAILED",
                "evidence": (
                    "Expected an iSCSI session, "
                    "but none was detected."
                ),
            }

        return {
            "check": "iscsi_session",
            "status": "NOT_APPLICABLE",
            "evidence": (
                "No active iSCSI session is "
                "currently expected."
            ),
        }

    return {
        "check": "iscsi_session",
        "status": "SESSION_PRESENT",
        "evidence": output,
    }


def build_storage_state(
    cinder,
    nova,
    libvirt,
    iscsi,
):
    nova_attached = (
        nova.get("status")
        == "ATTACHED"
    )

    return {
        "cinder": cinder,
        "nova": nova,
        "libvirt": libvirt,
        "iscsi": iscsi,
        "iSCSI_expected": nova_attached,
    }


def analyze_storage_consistency(
    state,
):
    cinder = state["cinder"]
    nova = state["nova"]
    libvirt = state["libvirt"]
    iscsi = state["iscsi"]

    findings = []

    unknown_layers = []

    if cinder.get("status") == "UNKNOWN":
        unknown_layers.append("Cinder")

    if nova.get("status") == "UNKNOWN":
        unknown_layers.append("Nova")

    if libvirt.get("status") == "UNKNOWN":
        unknown_layers.append("libvirt")

    if unknown_layers:

        findings.append({
            "severity": "WARNING",
            "classification":
                "VERIFICATION_INCOMPLETE",
            "message": (
                "One or more infrastructure layers "
                "could not be verified: "
                + ", ".join(unknown_layers)
            ),
        })

        return {
            "overall_status": "UNKNOWN",
            "findings": findings,
        }

    cinder_attached = (
        cinder.get("attachment_count", 0) > 0
    )

    nova_attached = (
        nova.get("status") == "ATTACHED"
    )

    libvirt_attached = (
        libvirt.get("status") == "ATTACHED"
    )

    iscsi_present = (
        iscsi.get("status")
        == "SESSION_PRESENT"
    )

    # --------------------------------------------------------
    # Completely unattached volume
    # --------------------------------------------------------

    if (
        not cinder_attached
        and not nova_attached
        and not libvirt_attached
        and not iscsi_present
    ):

        findings.append({
            "severity": "INFO",
            "classification":
                "CONSISTENT_UNATTACHED",
            "message": (
                "Cinder, Nova, libvirt and iSCSI "
                "consistently report no active "
                "volume attachment."
            ),
        })

        return {
            "overall_status": "CONSISTENT",
            "findings": findings,
        }

    # --------------------------------------------------------
    # Cinder says attached, Nova does not
    # --------------------------------------------------------

    if (
        cinder_attached
        and not nova_attached
    ):

        findings.append({
            "severity": "HIGH",
            "classification":
                "CONTROL_PLANE_INCONSISTENCY",
            "message": (
                "Cinder reports an attachment, "
                "but Nova does not."
            ),
        })

        return {
            "overall_status": "INCONSISTENT",
            "findings": findings,
        }

    # --------------------------------------------------------
    # Nova says attached, libvirt does not
    # --------------------------------------------------------

    if (
        nova_attached
        and not libvirt_attached
    ):

        findings.append({
            "severity": "HIGH",
            "classification":
                "ATTACHMENT_INCONSISTENCY",
            "message": (
                "Nova reports the volume as attached, "
                "but libvirt does not expose the disk."
            ),
        })

        return {
            "overall_status": "INCONSISTENT",
            "findings": findings,
        }

    # --------------------------------------------------------
    # Nova says attached but iSCSI is missing
    # --------------------------------------------------------

    if (
        nova_attached
        and not iscsi_present
    ):

        findings.append({
            "severity": "HIGH",
            "classification":
                "ISCSI_PATH_INCONSISTENCY",
            "message": (
                "Nova reports the volume as attached, "
                "but no iSCSI session is present."
            ),
        })

        return {
            "overall_status": "INCONSISTENT",
            "findings": findings,
        }

    # --------------------------------------------------------
    # libvirt sees disk but iSCSI absent
    # --------------------------------------------------------

    if (
        libvirt_attached
        and not iscsi_present
    ):

        findings.append({
            "severity": "MEDIUM",
            "classification":
                "STORAGE_PATH_INCONSISTENCY",
            "message": (
                "libvirt exposes the disk, but "
                "no iSCSI session is present."
            ),
        })

        return {
            "overall_status": "INCONSISTENT",
            "findings": findings,
        }

    # --------------------------------------------------------
    # No contradiction
    # --------------------------------------------------------

    findings.append({
        "severity": "INFO",
        "classification":
            "NO_CONTRADICTION_DETECTED",
        "message": (
            "No contradiction was detected "
            "between the verified infrastructure layers."
        ),
    })

    return {
        "overall_status": "CONSISTENT",
        "findings": findings,
    }


def verify_openstack_storage(
    volume_id,
    server_id,
    domain,
):
    cinder = verify_cinder_volume(
        volume_id
    )

    nova = verify_nova_attachment(
        server_id,
        volume_id,
    )

    expected_iscsi = (
        nova.get("status")
        == "ATTACHED"
    )

    libvirt = verify_libvirt_disk(
        domain,
        "vdb",
    )

    iscsi = verify_iscsi_session(
        expected=expected_iscsi
    )

    state = build_storage_state(
        cinder,
        nova,
        libvirt,
        iscsi,
    )

    analysis = analyze_storage_consistency(
        state
    )

    return {
        "overall_status":
            analysis["overall_status"],

        "state": state,

        "findings":
            analysis["findings"],
    }
