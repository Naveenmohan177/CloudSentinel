DEPENDENCY_GRAPH = {
    "horizon": [
        "keystone",
        "haproxy",
    ],

    "nova-api": [
        "keystone",
        "placement",
        "rabbitmq",
        "mariadb",
    ],

    "nova-compute": [
        "nova",
        "libvirt",
        "qemu-kvm",
        "neutron",
    ],

    "neutron": [
        "rabbitmq",
        "mariadb",
        "openvswitch",
    ],

    "cinder-api": [
        "keystone",
        "rabbitmq",
        "mariadb",
    ],

    "cinder-volume": [
        "cinder-api",
        "lvm",
        "iscsid",
    ],

    "glance": [
        "keystone",
        "mariadb",
    ],

    "iscsid": [
        "linux-kernel",
        "configfs",
        "iscsi-kernel-subsystem",
    ],
}


def get_dependencies(component):
    return DEPENDENCY_GRAPH.get(
        component,
        []
    )


def get_dependents(component):
    dependents = []

    for service, dependencies in DEPENDENCY_GRAPH.items():
        if component in dependencies:
            dependents.append(service)

    return dependents
