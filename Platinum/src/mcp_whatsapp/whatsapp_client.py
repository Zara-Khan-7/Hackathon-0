"""WhatsApp MCP client — subprocess wrapper for the WhatsApp server."""

from src.utils.mcp_registry import call_mcp


def list_chats() -> dict:
    """List all WhatsApp chats."""
    return call_mcp("whatsapp", "list_whatsapp_chats")


def read_chat(chat_id: str) -> dict:
    """Read messages from a specific chat."""
    return call_mcp("whatsapp", "read_whatsapp_chat", {"chat_id": chat_id})


def send_message(chat_id: str, message: str) -> dict:
    """Send a WhatsApp message (DANGEROUS — local only)."""
    return call_mcp("whatsapp", "send_whatsapp", {
        "chat_id": chat_id,
        "message": message,
    })
