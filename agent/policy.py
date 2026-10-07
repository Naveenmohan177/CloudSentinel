DESTRUCTIVE_OPERATIONS = {
    "delete",
    "destroy",
    "remove",
    "purge",
    "format",
}

CHANGE_OPERATIONS = {
    "restart",
    "stop",
    "start",
    "modify",
    "reload",
    "change",
}


def classify_action(action_name: str):
    name = action_name.lower()

    for operation in DESTRUCTIVE_OPERATIONS:
        if operation in name:
            return "BLOCKED"

    for operation in CHANGE_OPERATIONS:
        if operation in name:
            return "APPROVAL_REQUIRED"

    return "SAFE"
