from dataclasses import dataclass


@dataclass
class ChaosScenario:
    name: str
    target: str
    description: str
    risk: str
    command: list[str]


SCENARIOS = [
    ChaosScenario(
        name="iscsid-container-failure",
        target="iscsid",
        description="Simulate an unhealthy iSCSI container condition.",
        risk="LAB_ONLY",
        command=[
            "docker",
            "inspect",
            "iscsid",
        ],
    ),

    ChaosScenario(
        name="docker-container-down",
        target="docker",
        description="Simulate container availability failure.",
        risk="LAB_ONLY",
        command=[
            "docker",
            "ps",
        ],
    ),

    ChaosScenario(
        name="service-failure-simulation",
        target="systemd",
        description="Simulate a failed service using a synthetic event.",
        risk="SAFE",
        command=[
            "true",
        ],
    ),
]


def list_scenarios():
    return SCENARIOS


def get_scenario(name):
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario

    return None
