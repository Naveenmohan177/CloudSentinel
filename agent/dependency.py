from agent.openstack_topology import DEPENDENCY_GRAPH


def dependency_chain(component):
    visited = set()
    chain = []

    def walk(name, depth=0):
        if name in visited:
            return

        visited.add(name)

        chain.append({
            "component": name,
            "depth": depth,
        })

        for dependency in DEPENDENCY_GRAPH.get(
            name,
            [],
        ):
            walk(
                dependency,
                depth + 1,
            )

    walk(component)

    return chain


def affected_components(component):
    affected = []

    for service, dependencies in (
        DEPENDENCY_GRAPH.items()
    ):
        if component in dependencies:
            affected.append(service)

    return affected


def calculate_affected_components(
    findings,
    incident_components=None,
):
    components = set(
        incident_components or []
    )

    for finding in findings:

        classification = finding.get(
            "classification"
        )

        if classification == (
            "ATTACHMENT_INCONSISTENCY"
        ):
            components.update([
                "nova",
                "cinder",
                "libvirt",
                "qemu-kvm",
            ])

        elif classification == (
            "CONTROL_PLANE_INCONSISTENCY"
        ):
            components.update([
                "cinder",
                "nova",
            ])

        elif classification == (
            "ISCSI_PATH_INCONSISTENCY"
        ):
            components.update([
                "nova",
                "cinder-volume",
                "iscsid",
                "iscsi",
            ])

        elif classification == (
            "STORAGE_PATH_INCONSISTENCY"
        ):
            components.update([
                "libvirt",
                "qemu-kvm",
                "iscsid",
            ])

    return sorted(components)
