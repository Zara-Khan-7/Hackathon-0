"""WhatsApp MCP Server — JSON-RPC over stdio (LOCAL-ONLY).

Tools:
- list_whatsapp_chats (SAFE) — list all chats
- read_whatsapp_chat (SAFE) — read messages in a chat
- send_whatsapp (DANGEROUS) — send a message
"""

import json
import sys
import os

from src.mcp_whatsapp.mock_whatsapp import get_chats, get_messages, send_message

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

TOOLS = [
    {
        "name": "list_whatsapp_chats",
        "description": "List all WhatsApp chats with last message preview",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_whatsapp_chat",
        "description": "Read messages in a specific WhatsApp chat",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The chat ID to read"},
            },
            "required": ["chat_id"],
        },
    },
    {
        "name": "send_whatsapp",
        "description": "Send a WhatsApp message (DANGEROUS — requires approval)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The chat ID to send to"},
                "message": {"type": "string", "description": "Message text to send"},
            },
            "required": ["chat_id", "message"],
        },
    },
]


def handle_tool_call(name: str, arguments: dict) -> dict:
    """Handle a single tool call."""
    if name == "list_whatsapp_chats":
        chats = get_chats()
        return {"chats": chats, "count": len(chats)}

    elif name == "read_whatsapp_chat":
        chat_id = arguments.get("chat_id", "")
        messages = get_messages(chat_id)
        if not messages:
            return {"error": f"Chat not found: {chat_id}", "messages": []}
        return {"chat_id": chat_id, "messages": messages, "count": len(messages)}

    elif name == "send_whatsapp":
        chat_id = arguments.get("chat_id", "")
        message = arguments.get("message", "")

        if DRY_RUN:
            return {
                "status": "dry_run",
                "chat_id": chat_id,
                "message": message,
                "note": "Message NOT sent (dry-run mode)",
            }

        result = send_message(chat_id, message)
        return {"status": "sent", "result": result}

    else:
        raise ValueError(f"Unknown tool: {name}")


def handle_request(request: dict) -> dict:
    """Handle a JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id", 1)

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ai-employee-whatsapp", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}]
                },
            }
        except ValueError as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": str(e)},
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }


def main():
    """Read JSON-RPC requests from stdin, write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
