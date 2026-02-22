"""Tests for the Odoo MCP server."""

import json
import pytest
import os

# Force mock mode for tests
os.environ["ODOO_MOCK"] = "true"
os.environ["DRY_RUN"] = "true"

from src.mcp_odoo.odoo_server import OdooConnection, handle_request, TOOLS


class TestOdooConnection:
    """Test the OdooConnection wrapper in mock mode."""

    @pytest.fixture
    def conn(self):
        c = OdooConnection()
        c.mock = True
        c.dry_run = True
        return c

    def test_list_invoices_all(self, conn):
        invoices = conn.list_invoices()
        assert len(invoices) >= 3
        assert all("id" in inv for inv in invoices)

    def test_list_invoices_filter_state(self, conn):
        drafts = conn.list_invoices(state="draft")
        assert all(inv["state"] == "draft" for inv in drafts)

    def test_list_invoices_filter_move_type(self, conn):
        customer = conn.list_invoices(move_type="out_invoice")
        assert all(inv["move_type"] == "out_invoice" for inv in customer)

    def test_read_invoice(self, conn):
        inv = conn.read_invoice(101)
        assert inv["id"] == 101
        assert inv["name"] == "INV/2026/0001"
        assert inv["partner_name"] == "Acme Corporation"

    def test_read_invoice_not_found(self, conn):
        inv = conn.read_invoice(999)
        assert "error" in inv

    def test_create_invoice_draft(self, conn):
        lines = [
            {"description": "Consulting", "quantity": 10, "price_unit": 150},
            {"description": "Setup fee", "quantity": 1, "price_unit": 500},
        ]
        result = conn.create_invoice_draft(partner_id=1, lines=lines)
        assert result["state"] == "draft"
        assert result["amount_total"] == 2000.0
        assert result["partner_id"] == 1

    def test_post_invoice(self, conn):
        result = conn.post_invoice(101)
        assert result["state"] == "posted"

    def test_list_partners(self, conn):
        partners = conn.list_partners()
        assert len(partners) >= 3

    def test_list_partners_companies_only(self, conn):
        companies = conn.list_partners(is_company=True)
        assert all(p["is_company"] for p in companies)

    def test_read_transactions(self, conn):
        txns = conn.read_transactions()
        assert len(txns) >= 2
        assert all("amount" in t for t in txns)


class TestMCPProtocol:
    """Test JSON-RPC protocol handling."""

    def _mock_odoo(self):
        conn = OdooConnection()
        conn.mock = True
        conn.dry_run = True
        return conn

    def test_initialize(self):
        request = {"jsonrpc": "2.0", "method": "initialize", "id": 1}
        response = handle_request(request, self._mock_odoo())
        assert response["result"]["serverInfo"]["name"] == "ai-employee-odoo"

    def test_tools_list(self):
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        response = handle_request(request, self._mock_odoo())
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "list_invoices" in tool_names
        assert "create_invoice_draft" in tool_names
        assert "post_invoice" in tool_names
        assert "list_partners" in tool_names
        assert "read_transactions" in tool_names

    def test_tools_call_list_invoices(self):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "list_invoices", "arguments": {}},
        }
        response = handle_request(request, self._mock_odoo())
        assert not response["result"]["isError"]
        data = json.loads(response["result"]["content"][0]["text"])
        assert isinstance(data, list)

    def test_unknown_method(self):
        request = {"jsonrpc": "2.0", "method": "foo/bar", "id": 1}
        response = handle_request(request, self._mock_odoo())
        assert "error" in response

    def test_unknown_tool(self):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "nonexistent_tool", "arguments": {}},
        }
        response = handle_request(request, self._mock_odoo())
        assert "error" in response
