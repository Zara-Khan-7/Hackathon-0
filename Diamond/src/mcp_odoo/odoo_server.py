"""
MCP JSON-RPC server for Odoo ERP integration.

Provides tools for invoice management, partner lookup, and transaction reading
via Odoo's XML-RPC/JSON-RPC interface. Supports mock mode for development
without a running Odoo instance.

Usage:
    echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m src.mcp_odoo.odoo_server
"""

import json
import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("mcp_odoo")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

# ---------------------------------------------------------------------------
# Mock data for development / testing
# ---------------------------------------------------------------------------

MOCK_PARTNERS = [
    {"id": 1, "name": "Acme Corporation", "email": "billing@acme.com", "phone": "+1-555-0100", "is_company": True, "city": "San Francisco", "country": "US"},
    {"id": 2, "name": "TechStart Inc.", "email": "finance@techstart.io", "phone": "+1-555-0200", "is_company": True, "city": "Austin", "country": "US"},
    {"id": 3, "name": "Jane Smith", "email": "jane@example.com", "phone": "+1-555-0300", "is_company": False, "city": "New York", "country": "US"},
    {"id": 4, "name": "Global Supplies Ltd", "email": "accounts@globalsupplies.co.uk", "phone": "+44-20-7946-0958", "is_company": True, "city": "London", "country": "GB"},
]

MOCK_INVOICES = [
    {"id": 101, "name": "INV/2026/0001", "partner_id": 1, "partner_name": "Acme Corporation", "state": "posted", "amount_total": 5000.00, "amount_residual": 5000.00, "invoice_date": "2026-02-01", "invoice_date_due": "2026-03-01", "move_type": "out_invoice", "payment_state": "not_paid"},
    {"id": 102, "name": "INV/2026/0002", "partner_id": 2, "partner_name": "TechStart Inc.", "state": "posted", "amount_total": 12500.00, "amount_residual": 0.00, "invoice_date": "2026-01-15", "invoice_date_due": "2026-02-15", "move_type": "out_invoice", "payment_state": "paid"},
    {"id": 103, "name": "INV/2026/0003", "partner_id": 4, "partner_name": "Global Supplies Ltd", "state": "draft", "amount_total": 3200.00, "amount_residual": 3200.00, "invoice_date": "2026-02-15", "invoice_date_due": "2026-03-15", "move_type": "out_invoice", "payment_state": "not_paid"},
    {"id": 104, "name": "BILL/2026/0001", "partner_id": 4, "partner_name": "Global Supplies Ltd", "state": "posted", "amount_total": 1800.00, "amount_residual": 1800.00, "invoice_date": "2026-02-10", "invoice_date_due": "2026-03-10", "move_type": "in_invoice", "payment_state": "not_paid"},
]

MOCK_TRANSACTIONS = [
    {"id": 201, "date": "2026-02-15", "name": "Customer Payment - Acme", "ref": "PAY/2026/0001", "amount": 2500.00, "partner_name": "Acme Corporation", "journal": "Bank", "state": "posted"},
    {"id": 202, "date": "2026-02-14", "name": "Customer Payment - TechStart", "ref": "PAY/2026/0002", "amount": 12500.00, "partner_name": "TechStart Inc.", "journal": "Bank", "state": "posted"},
    {"id": 203, "date": "2026-02-13", "name": "Supplier Payment - Global Supplies", "ref": "PAY/2026/0003", "amount": -900.00, "partner_name": "Global Supplies Ltd", "journal": "Bank", "state": "posted"},
    {"id": 204, "date": "2026-02-12", "name": "Office Supplies", "ref": "MISC/2026/0001", "amount": -245.50, "partner_name": "", "journal": "Cash", "state": "posted"},
]

# ---------------------------------------------------------------------------
# Odoo connection helper
# ---------------------------------------------------------------------------

class OdooConnection:
    """Wrapper around odoorpc for Odoo XML-RPC calls."""

    def __init__(self):
        self.host = os.getenv("ODOO_HOST", "localhost")
        self.port = int(os.getenv("ODOO_PORT", "8069"))
        self.db = os.getenv("ODOO_DB", "odoo")
        self.user = os.getenv("ODOO_USER", "admin")
        self.password = os.getenv("ODOO_PASSWORD", "admin")
        self.mock = os.getenv("ODOO_MOCK", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self._odoo = None

    def connect(self):
        if self.mock:
            logger.info("Odoo running in MOCK mode — no real connection")
            return
        try:
            import odoorpc
            self._odoo = odoorpc.ODOO(self.host, port=self.port)
            self._odoo.login(self.db, self.user, self.password)
            logger.info(f"Connected to Odoo at {self.host}:{self.port} db={self.db}")
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            logger.info("Falling back to MOCK mode")
            self.mock = True

    def list_invoices(self, state=None, move_type=None, limit=50):
        if self.mock:
            results = MOCK_INVOICES[:]
            if state:
                results = [inv for inv in results if inv["state"] == state]
            if move_type:
                results = [inv for inv in results if inv["move_type"] == move_type]
            return results[:limit]

        InvModel = self._odoo.env["account.move"]
        domain = [("move_type", "in", ["out_invoice", "in_invoice"])]
        if state:
            domain.append(("state", "=", state))
        if move_type:
            domain.append(("move_type", "=", move_type))
        ids = InvModel.search(domain, limit=limit)
        fields = ["name", "partner_id", "state", "amount_total", "amount_residual",
                   "invoice_date", "invoice_date_due", "move_type", "payment_state"]
        records = InvModel.read(ids, fields)
        for r in records:
            if r.get("partner_id"):
                r["partner_name"] = r["partner_id"][1]
                r["partner_id"] = r["partner_id"][0]
        return records

    def read_invoice(self, invoice_id):
        if self.mock:
            for inv in MOCK_INVOICES:
                if inv["id"] == invoice_id:
                    return inv
            return {"error": f"Invoice {invoice_id} not found"}

        InvModel = self._odoo.env["account.move"]
        fields = ["name", "partner_id", "state", "amount_total", "amount_residual",
                   "invoice_date", "invoice_date_due", "move_type", "payment_state",
                   "invoice_line_ids", "narration"]
        records = InvModel.read([invoice_id], fields)
        if not records:
            return {"error": f"Invoice {invoice_id} not found"}
        rec = records[0]
        if rec.get("partner_id"):
            rec["partner_name"] = rec["partner_id"][1]
            rec["partner_id"] = rec["partner_id"][0]
        return rec

    def create_invoice_draft(self, partner_id, lines, move_type="out_invoice"):
        if self.mock or self.dry_run:
            new_id = max(inv["id"] for inv in MOCK_INVOICES) + 1
            total = sum(line.get("price_unit", 0) * line.get("quantity", 1) for line in lines)
            result = {
                "id": new_id,
                "name": f"INV/2026/{new_id:04d}",
                "partner_id": partner_id,
                "state": "draft",
                "amount_total": total,
                "move_type": move_type,
                "lines": lines,
                "dry_run": self.dry_run,
                "mock": self.mock,
            }
            logger.info(f"[{'DRY-RUN' if self.dry_run else 'MOCK'}] Created draft invoice: {result['name']} total={total}")
            return result

        InvModel = self._odoo.env["account.move"]
        inv_lines = []
        for line in lines:
            inv_lines.append((0, 0, {
                "name": line.get("description", "Service"),
                "quantity": line.get("quantity", 1),
                "price_unit": line.get("price_unit", 0),
            }))
        inv_id = InvModel.create({
            "partner_id": partner_id,
            "move_type": move_type,
            "invoice_line_ids": inv_lines,
        })
        return self.read_invoice(inv_id)

    def post_invoice(self, invoice_id):
        if self.mock or self.dry_run:
            inv = self.read_invoice(invoice_id)
            if isinstance(inv, dict) and "error" in inv:
                return inv
            inv["state"] = "posted"
            logger.info(f"[{'DRY-RUN' if self.dry_run else 'MOCK'}] Posted invoice {inv.get('name', invoice_id)}")
            return inv

        InvModel = self._odoo.env["account.move"]
        InvModel.browse(invoice_id).action_post()
        return self.read_invoice(invoice_id)

    def list_partners(self, is_company=None, limit=50):
        if self.mock:
            results = MOCK_PARTNERS[:]
            if is_company is not None:
                results = [p for p in results if p["is_company"] == is_company]
            return results[:limit]

        PartnerModel = self._odoo.env["res.partner"]
        domain = []
        if is_company is not None:
            domain.append(("is_company", "=", is_company))
        ids = PartnerModel.search(domain, limit=limit)
        fields = ["name", "email", "phone", "is_company", "city", "country_id"]
        records = PartnerModel.read(ids, fields)
        for r in records:
            if r.get("country_id"):
                r["country"] = r["country_id"][1]
                r["country_id"] = r["country_id"][0]
        return records

    def read_transactions(self, days=30, limit=100):
        if self.mock:
            return MOCK_TRANSACTIONS[:limit]

        MoveModel = self._odoo.env["account.move.line"]
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        domain = [
            ("date", ">=", date_from),
            ("journal_id.type", "in", ["bank", "cash"]),
        ]
        ids = MoveModel.search(domain, limit=limit)
        fields = ["date", "name", "ref", "debit", "credit", "partner_id", "journal_id"]
        records = MoveModel.read(ids, fields)
        results = []
        for r in records:
            results.append({
                "id": r["id"],
                "date": r["date"],
                "name": r.get("name", ""),
                "ref": r.get("ref", ""),
                "amount": r.get("debit", 0) - r.get("credit", 0),
                "partner_name": r["partner_id"][1] if r.get("partner_id") else "",
                "journal": r["journal_id"][1] if r.get("journal_id") else "",
            })
        return results


# ---------------------------------------------------------------------------
# MCP Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "list_invoices",
        "description": "List invoices from Odoo ERP. Optionally filter by state (draft/posted/cancel) and move_type (out_invoice/in_invoice).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "enum": ["draft", "posted", "cancel"], "description": "Filter by invoice state"},
                "move_type": {"type": "string", "enum": ["out_invoice", "in_invoice"], "description": "out_invoice=customer, in_invoice=vendor"},
                "limit": {"type": "integer", "default": 50, "description": "Max results"},
            },
        },
    },
    {
        "name": "read_invoice",
        "description": "Read a specific invoice by ID from Odoo ERP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer", "description": "The Odoo invoice ID"},
            },
            "required": ["invoice_id"],
        },
    },
    {
        "name": "create_invoice_draft",
        "description": "Create a new draft invoice in Odoo. Requires HITL approval before posting.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "partner_id": {"type": "integer", "description": "Odoo partner (customer/vendor) ID"},
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number", "default": 1},
                            "price_unit": {"type": "number"},
                        },
                        "required": ["description", "price_unit"],
                    },
                    "description": "Invoice line items",
                },
                "move_type": {"type": "string", "enum": ["out_invoice", "in_invoice"], "default": "out_invoice"},
            },
            "required": ["partner_id", "lines"],
        },
    },
    {
        "name": "post_invoice",
        "description": "Post (confirm) a draft invoice in Odoo. This makes it official and sends to customer. REQUIRES prior HITL approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer", "description": "The Odoo invoice ID to post"},
            },
            "required": ["invoice_id"],
        },
    },
    {
        "name": "list_partners",
        "description": "List partners (customers/vendors) from Odoo ERP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "is_company": {"type": "boolean", "description": "Filter: true=companies only, false=individuals only"},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "read_transactions",
        "description": "Read recent bank/cash transactions from Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30, "description": "Look back N days"},
                "limit": {"type": "integer", "default": 100},
            },
        },
    },
]

# ---------------------------------------------------------------------------
# JSON-RPC request handling
# ---------------------------------------------------------------------------

def handle_request(request: dict, odoo: OdooConnection) -> dict:
    """Process a JSON-RPC 2.0 request and return a response."""
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ai-employee-odoo", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        return _call_tool(req_id, tool_name, arguments, odoo)

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def _call_tool(req_id, tool_name: str, arguments: dict, odoo: OdooConnection) -> dict:
    """Dispatch a tool call to the Odoo connection."""
    try:
        if tool_name == "list_invoices":
            result = odoo.list_invoices(
                state=arguments.get("state"),
                move_type=arguments.get("move_type"),
                limit=arguments.get("limit", 50),
            )
        elif tool_name == "read_invoice":
            result = odoo.read_invoice(arguments["invoice_id"])
        elif tool_name == "create_invoice_draft":
            result = odoo.create_invoice_draft(
                partner_id=arguments["partner_id"],
                lines=arguments["lines"],
                move_type=arguments.get("move_type", "out_invoice"),
            )
        elif tool_name == "post_invoice":
            result = odoo.post_invoice(arguments["invoice_id"])
        elif tool_name == "list_partners":
            result = odoo.list_partners(
                is_company=arguments.get("is_company"),
                limit=arguments.get("limit", 50),
            )
        elif tool_name == "read_transactions":
            result = odoo.read_transactions(
                days=arguments.get("days", 30),
                limit=arguments.get("limit", 100),
            )
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, default=str)}],
                "isError": False,
            },
        }
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            },
        }


# ---------------------------------------------------------------------------
# Main: stdio JSON-RPC loop
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server reading JSON-RPC from stdin, writing to stdout."""
    odoo = OdooConnection()
    odoo.connect()

    logger.info("Odoo MCP server started (reading from stdin)")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request, odoo)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
