"""Domain routing — determines which agent (cloud/local) handles each task.

Maps task prefixes to required roles and cloud-specific actions.
"""

from src.config.agent_config import AgentRole


# Cloud action types
CLOUD_ACTION_DRAFT = "draft_only"   # Cloud creates a draft, routes to approval
CLOUD_ACTION_FULL = "full"          # Cloud can fully handle
CLOUD_ACTION_SKIP = "skip"          # Cloud must skip (local-only)

# Routing table: prefix → {cloud_action, local_action, reason}
ROUTING_TABLE = {
    "EMAIL_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "SMTP credentials are local-only",
    },
    "LINKEDIN_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "Session is local-only",
    },
    "FACEBOOK_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "API key is local-only",
    },
    "INSTAGRAM_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "Session is local-only",
    },
    "TWITTER_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "API key is local-only",
    },
    "WHATSAPP_": {
        "cloud": CLOUD_ACTION_SKIP,
        "local": "full",
        "reason": "Session files never sync to cloud",
    },
    "PAYMENT_": {
        "cloud": CLOUD_ACTION_SKIP,
        "local": "full",
        "reason": "Banking credentials never sync to cloud",
    },
    "SCHEDULE_": {
        "cloud": CLOUD_ACTION_FULL,
        "local": "full",
        "reason": "Either agent can schedule",
    },
    "ODOO_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "Posting is dangerous, cloud drafts only",
    },
    "AUDIT_": {
        "cloud": CLOUD_ACTION_FULL,
        "local": "full",
        "reason": "Read-only, either can audit",
    },
    "ERROR_": {
        "cloud": CLOUD_ACTION_FULL,
        "local": "full",
        "reason": "Either can handle errors",
    },
    "APPROVE_": {
        "cloud": CLOUD_ACTION_SKIP,
        "local": "full",
        "reason": "Approvals require human (local terminal)",
    },
    "EXECUTE_": {
        "cloud": CLOUD_ACTION_SKIP,
        "local": "full",
        "reason": "Only local executes approved actions",
    },
    "SOCIAL_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "Social posting requires local API keys",
    },
    "SALESPOST_": {
        "cloud": CLOUD_ACTION_DRAFT,
        "local": "full",
        "reason": "Posting requires local credentials",
    },
}


def get_prefix(filename: str) -> str | None:
    """Extract the task prefix from a filename (e.g., 'EMAIL_' from 'EMAIL_mock_001.md')."""
    for prefix in ROUTING_TABLE:
        if filename.startswith(prefix):
            return prefix
    return None


def should_handle(filename: str, role: AgentRole) -> bool:
    """Check if an agent with the given role should handle this task.

    Gold role handles everything (backward-compatible).
    """
    if role == AgentRole.GOLD:
        return True

    prefix = get_prefix(filename)
    if prefix is None:
        # Unknown prefix — cloud handles cautiously (draft), local handles fully
        return True

    route = ROUTING_TABLE[prefix]
    role_key = role.value  # "cloud" or "local"
    action = route.get(role_key, "full")
    return action != CLOUD_ACTION_SKIP


def get_cloud_action(filename: str) -> str:
    """Get the cloud action for a given task filename.

    Returns: 'draft_only', 'full', or 'skip'
    """
    prefix = get_prefix(filename)
    if prefix is None:
        return CLOUD_ACTION_DRAFT  # default: draft unknown tasks

    return ROUTING_TABLE[prefix]["cloud"]


def get_routing_reason(filename: str) -> str:
    """Get the reason string for why a task is routed a certain way."""
    prefix = get_prefix(filename)
    if prefix is None:
        return "Unknown prefix — default routing"
    return ROUTING_TABLE[prefix]["reason"]


def list_skipped_prefixes(role: AgentRole) -> list[str]:
    """List all prefixes that are skipped for the given role."""
    role_key = role.value
    return [
        prefix for prefix, route in ROUTING_TABLE.items()
        if route.get(role_key) == CLOUD_ACTION_SKIP
    ]
