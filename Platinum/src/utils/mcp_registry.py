"""Unified MCP server registry and caller — Platinum Tier.

Routes tool calls to the correct MCP server via subprocess.
Includes tool policy enforcement for cloud/local role separation.

Usage:
    from src.utils.mcp_registry import call_mcp
    result = call_mcp("email", "send_email", {"to": "x@y.com", "subject": "Hi", "body": "Hello"})
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

from src.utils.retry import with_retry

logger = logging.getLogger("ai_employee")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Registry: server_name → module path
MCP_SERVERS = {
    "email": "src.mcp_email.email_server",
    "odoo": "src.mcp_odoo.odoo_server",
    "social": "src.mcp_social.social_server",
    "whatsapp": "src.mcp_whatsapp.whatsapp_server",
    "payment": "src.mcp_payment.payment_server",
}


def _raw_call(server_module: str, tool_name: str, arguments: dict, timeout: int = 30) -> dict:
    """Spawn a subprocess for the MCP server and send a single tool call."""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {"name": tool_name, "arguments": arguments},
    }
    request_json = json.dumps(request) + "\n"

    proc = subprocess.run(
        [sys.executable, "-m", server_module],
        input=request_json,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )

    for line in proc.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        response = json.loads(line)
        if "result" in response:
            content = response["result"].get("content", [])
            if content:
                return json.loads(content[0].get("text", "{}"))
        elif "error" in response:
            raise RuntimeError(response["error"].get("message", "MCP server error"))

    raise RuntimeError("No valid response from MCP server")


@with_retry(max_attempts=2, backoff_factor=2)
def call_mcp(server_name: str, tool_name: str, arguments: dict = None,
             timeout: int = 30, role: str | None = None) -> dict:
    """Call a tool on a registered MCP server.

    Args:
        server_name: One of "email", "odoo", "social", "whatsapp", "payment"
        tool_name: The tool to invoke (e.g. "send_email", "list_invoices")
        arguments: Tool arguments dict
        timeout: Subprocess timeout in seconds
        role: Agent role for policy enforcement (cloud/local/gold)

    Returns:
        The tool result dict

    Raises:
        ValueError: If server_name is not registered
        PermissionError: If tool is blocked by policy for this role
        RetryExhausted: If all retry attempts fail
    """
    if server_name not in MCP_SERVERS:
        raise ValueError(
            f"Unknown MCP server: {server_name}. "
            f"Available: {list(MCP_SERVERS.keys())}"
        )

    # Enforce tool policy if role is provided
    if role:
        from src.config.tool_policy import is_allowed, is_local_only_server
        from src.config.agent_config import AgentRole

        agent_role = AgentRole(role)

        if is_local_only_server(server_name) and agent_role == AgentRole.CLOUD:
            raise PermissionError(
                f"Server '{server_name}' is local-only, not available on cloud"
            )

        if not is_allowed(tool_name, agent_role):
            raise PermissionError(
                f"Tool '{tool_name}' is blocked for role '{role}'"
            )

    server_module = MCP_SERVERS[server_name]
    logger.info(f"MCP call: {server_name}.{tool_name}({arguments})")

    result = _raw_call(server_module, tool_name, arguments or {}, timeout=timeout)
    logger.info(f"MCP result: {server_name}.{tool_name} → {str(result)[:200]}")
    return result


def list_servers(role: str | None = None) -> dict[str, str]:
    """Return the registry of MCP server names to modules.

    If role is provided, filters out servers not available for that role.
    """
    servers = dict(MCP_SERVERS)

    if role:
        from src.config.tool_policy import is_local_only_server
        from src.config.agent_config import AgentRole

        agent_role = AgentRole(role)
        if agent_role == AgentRole.CLOUD:
            servers = {
                name: module for name, module in servers.items()
                if not is_local_only_server(name)
            }

    return servers


def list_tools(server_name: str, timeout: int = 10) -> list[dict]:
    """List available tools on a specific MCP server."""
    if server_name not in MCP_SERVERS:
        raise ValueError(f"Unknown MCP server: {server_name}")

    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
    }
    request_json = json.dumps(request) + "\n"

    proc = subprocess.run(
        [sys.executable, "-m", MCP_SERVERS[server_name]],
        input=request_json,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )

    for line in proc.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        response = json.loads(line)
        if "result" in response:
            return response["result"].get("tools", [])

    return []
