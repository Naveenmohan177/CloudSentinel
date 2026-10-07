from dataclasses import dataclass

from agent.policy import classify_action


@dataclass
class RecoveryAction:
    name: str
    reason: str
    command: list[str]


def plan_recovery(incident: str):
    actions = []

    if incident == "kolla-iscsid-container failure":
        actions.append(
            RecoveryAction(
                name="Collect container diagnostics",
                reason="Gather additional evidence before changing infrastructure.",
                command=[
                    "docker",
                    "logs",
                    "--tail",
                    "100",
                    "iscsid",
                ],
            )
        )

        actions.append(
            RecoveryAction(
                name="Inspect iscsid container",
                reason="Verify container state and runtime configuration.",
                command=[
                    "docker",
                    "inspect",
                    "iscsid",
                ],
            )
        )

        actions.append(
            RecoveryAction(
                name="Restart iscsid container",
                reason="Restart changes infrastructure state and may affect Cinder storage operations.",
                command=[
                    "docker",
                    "restart",
                    "iscsid",
                ],
            )
        )

        actions.append(
            RecoveryAction(
                name="Delete Cinder volume",
                reason="Destructive storage operation must never be automated.",
                command=[
                    "openstack",
                    "volume",
                    "delete",
                    "<volume>",
                ],
            )
        )

    return actions


def generate_recovery_plan(incident: str):
    actions = plan_recovery(incident)

    recovery_plan = []

    for action in actions:
        risk = classify_action(action.name)

        recovery_plan.append(
            {
                "action": action.name,
                "risk": risk,
                "reason": action.reason,
                "command": action.command,
                "execution": (
                    "DRY_RUN"
                    if risk == "SAFE"
                    else "NOT_EXECUTED"
                ),
            }
        )

    return recovery_plan
