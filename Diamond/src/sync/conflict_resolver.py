"""Deterministic merge conflict resolution for git sync.

Mock implementation — resolves conflicts by folder convention:
- Needs_Action: keep incoming (theirs) — cloud watchers create
- In_Progress: keep local (ours) — whoever claimed owns it
- Logs: union (both) — both sides contribute
- Done: union (both)
"""

from src.utils.logger import log_action


# Resolution strategy per folder
STRATEGIES = {
    "Needs_Action": "theirs",
    "In_Progress": "ours",
    "Pending_Approval": "theirs",
    "Done": "union",
    "Logs": "union",
    "Errors": "union",
}


def get_strategy(folder_name: str) -> str:
    """Get the merge strategy for a folder.

    Returns: 'ours', 'theirs', or 'union'
    """
    return STRATEGIES.get(folder_name, "theirs")


def resolve_conflicts(folder_name: str, local_content: str, remote_content: str) -> str:
    """Resolve a mock merge conflict between local and remote content.

    Args:
        folder_name: The folder where the conflict occurred
        local_content: Our (local) version
        remote_content: Their (remote) version

    Returns:
        The resolved content string
    """
    strategy = get_strategy(folder_name)

    if strategy == "ours":
        log_action(
            "[MOCK] Conflict resolved",
            f"{folder_name}: keeping ours",
            "conflict",
        )
        return local_content

    elif strategy == "theirs":
        log_action(
            "[MOCK] Conflict resolved",
            f"{folder_name}: keeping theirs",
            "conflict",
        )
        return remote_content

    else:  # union
        log_action(
            "[MOCK] Conflict resolved",
            f"{folder_name}: union merge",
            "conflict",
        )
        return _union_merge(local_content, remote_content)


def _union_merge(local: str, remote: str) -> str:
    """Union merge: combine unique lines from both versions."""
    local_lines = set(local.splitlines())
    remote_lines = remote.splitlines()

    # Start with remote, add unique local lines at end
    result_lines = list(remote.splitlines())
    for line in local.splitlines():
        if line not in local_lines & set(remote_lines):
            result_lines.append(line)

    return "\n".join(dict.fromkeys(result_lines)) + "\n"
