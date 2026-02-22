"""MCP Email Client — helper to call the MCP email server from scripts."""

import json
import subprocess
import sys
from pathlib import Path

from src.utils.logger import log_action, log_error

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call an MCP email server tool and return the result.

    Spawns the MCP server as a subprocess, sends a JSON-RPC request,
    and returns the parsed response.
    """
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1,
    }

    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.mcp_email.email_server"],
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )

        if result.returncode != 0 and result.stderr:
            log_error("MCP server error", result.stderr[:500], "mcp_client")

        # Parse the last non-empty line of stdout as JSON response
        for line in reversed(result.stdout.strip().split("\n")):
            if line.strip():
                return json.loads(line)

        return {"error": "No response from MCP server"}

    except subprocess.TimeoutExpired:
        log_error("MCP server timeout", "", "mcp_client")
        return {"error": "MCP server timed out"}
    except Exception as e:
        log_error("MCP client error", str(e), "mcp_client")
        return {"error": str(e)}


def send_email(to: str, subject: str, body: str, cc: str = "") -> dict:
    """Send an email via MCP server."""
    return call_mcp_tool("send_email", {"to": to, "subject": subject, "body": body, "cc": cc})


def draft_email(to: str, subject: str, body: str, cc: str = "") -> dict:
    """Create an email draft via MCP server."""
    return call_mcp_tool("draft_email", {"to": to, "subject": subject, "body": body, "cc": cc})


def list_drafts() -> dict:
    """List all email drafts via MCP server."""
    return call_mcp_tool("list_drafts", {})
