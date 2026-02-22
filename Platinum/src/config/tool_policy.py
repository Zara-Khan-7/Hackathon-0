"""Tool safety policy — classifies MCP tools as SAFE, DRAFT, or DANGEROUS.

Enforces that cloud agents can only call SAFE + DRAFT tools.
Local agents can call ALL tools.
"""

from src.config.agent_config import AgentRole

# Safety classifications
SAFE = "safe"           # read-only, no side effects
DRAFT = "draft"         # creates drafts, no external action
DANGEROUS = "dangerous" # sends/posts/pays — requires local agent

TOOL_POLICY = {
    # Email MCP
    "send_email": DANGEROUS,
    "draft_email": DRAFT,
    "list_drafts": SAFE,

    # Odoo MCP
    "list_invoices": SAFE,
    "read_invoice": SAFE,
    "create_invoice_draft": DRAFT,
    "post_invoice": DANGEROUS,
    "list_partners": SAFE,
    "read_transactions": SAFE,

    # Social MCP
    "post_facebook": DANGEROUS,
    "post_instagram": DANGEROUS,
    "post_twitter": DANGEROUS,
    "draft_social_post": DRAFT,
    "get_social_summary": SAFE,

    # WhatsApp MCP (LOCAL-ONLY server)
    "list_whatsapp_chats": SAFE,
    "read_whatsapp_chat": SAFE,
    "send_whatsapp": DANGEROUS,

    # Payment MCP (LOCAL-ONLY server)
    "list_accounts": SAFE,
    "get_balance": SAFE,
    "list_transactions": SAFE,
    "initiate_payment": DANGEROUS,
    "payment_status": SAFE,
}

# MCP servers that only run on local
LOCAL_ONLY_SERVERS = {"whatsapp", "payment"}


def get_classification(tool_name: str) -> str:
    """Get the safety classification for a tool.

    Returns SAFE, DRAFT, or DANGEROUS. Defaults to DANGEROUS for unknown tools.
    """
    return TOOL_POLICY.get(tool_name, DANGEROUS)


def is_allowed(tool_name: str, role: AgentRole) -> bool:
    """Check if a tool is allowed for the given agent role.

    - Gold/Local: ALL tools allowed
    - Cloud: only SAFE + DRAFT tools allowed
    """
    if role in (AgentRole.LOCAL, AgentRole.GOLD):
        return True

    classification = get_classification(tool_name)
    return classification in (SAFE, DRAFT)


def get_blocked_tools(role: AgentRole) -> list[str]:
    """List all tools blocked for the given role."""
    return [
        tool for tool, classification in TOOL_POLICY.items()
        if not is_allowed(tool, role)
    ]


def get_allowed_tools(role: AgentRole) -> list[str]:
    """List all tools allowed for the given role."""
    return [
        tool for tool in TOOL_POLICY
        if is_allowed(tool, role)
    ]


def is_local_only_server(server_name: str) -> bool:
    """Check if an MCP server only runs on local machines."""
    return server_name in LOCAL_ONLY_SERVERS
