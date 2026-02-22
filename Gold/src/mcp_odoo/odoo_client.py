"""
Helper wrapper for calling the Odoo MCP server as a subprocess.

Usage:
    from src.mcp_odoo.odoo_client import OdooClient
    client = OdooClient()
    invoices = client.list_invoices(state="draft")
"""

import json
import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger("odoo_client")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class OdooClient:
    """Client wrapper that spawns the Odoo MCP server as a subprocess."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.server_module = "src.mcp_odoo.odoo_server"

    def call_mcp_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Call an MCP tool on the Odoo server via subprocess."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": tool_name, "arguments": arguments or {}},
        }
        request_json = json.dumps(request) + "\n"

        try:
            proc = subprocess.run(
                [sys.executable, "-m", self.server_module],
                input=request_json,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(PROJECT_ROOT),
            )
            for line in proc.stdout.strip().split("\n"):
                if line.strip():
                    response = json.loads(line)
                    if "result" in response:
                        content = response["result"].get("content", [])
                        if content:
                            return json.loads(content[0].get("text", "{}"))
                    elif "error" in response:
                        return {"error": response["error"].get("message", "Unknown error")}
            return {"error": "No valid response from Odoo MCP server"}
        except subprocess.TimeoutExpired:
            return {"error": f"Odoo MCP server timed out after {self.timeout}s"}
        except Exception as e:
            return {"error": f"Odoo MCP client error: {e}"}

    def list_invoices(self, state=None, move_type=None, limit=50):
        args = {"limit": limit}
        if state:
            args["state"] = state
        if move_type:
            args["move_type"] = move_type
        return self.call_mcp_tool("list_invoices", args)

    def read_invoice(self, invoice_id: int):
        return self.call_mcp_tool("read_invoice", {"invoice_id": invoice_id})

    def create_invoice_draft(self, partner_id: int, lines: list, move_type="out_invoice"):
        return self.call_mcp_tool("create_invoice_draft", {
            "partner_id": partner_id,
            "lines": lines,
            "move_type": move_type,
        })

    def post_invoice(self, invoice_id: int):
        return self.call_mcp_tool("post_invoice", {"invoice_id": invoice_id})

    def list_partners(self, is_company=None, limit=50):
        args = {"limit": limit}
        if is_company is not None:
            args["is_company"] = is_company
        return self.call_mcp_tool("list_partners", args)

    def read_transactions(self, days=30, limit=100):
        return self.call_mcp_tool("read_transactions", {"days": days, "limit": limit})
