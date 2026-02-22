"""Tests for src.mcp_payment — Payment MCP server and mock data."""

import json
import pytest

from src.mcp_payment.mock_payment import (
    get_accounts, get_balance, get_transactions,
    initiate_payment, get_payment_status, MOCK_PAYMENTS,
)
from src.mcp_payment.payment_server import handle_request, handle_tool_call


class TestMockPayment:
    def test_get_accounts(self):
        accounts = get_accounts()
        assert len(accounts) == 2
        assert all("account_id" in a for a in accounts)

    def test_get_balance(self):
        result = get_balance("acc_001")
        assert result is not None
        assert result["balance"] == 125000.00

    def test_get_balance_not_found(self):
        result = get_balance("nonexistent")
        assert result is None

    def test_get_transactions_all(self):
        txns = get_transactions()
        assert len(txns) == 4

    def test_get_transactions_filtered(self):
        txns = get_transactions("acc_001")
        assert len(txns) == 3
        assert all(t["account_id"] == "acc_001" for t in txns)

    def test_initiate_payment(self):
        before = len(MOCK_PAYMENTS)
        result = initiate_payment("acc_001", "Test Vendor", "AE123456", 100.0, "TEST-001")
        assert result["status"] == "pending_mock"
        assert len(MOCK_PAYMENTS) == before + 1

    def test_payment_status(self):
        result = initiate_payment("acc_001", "Test", "AE111", 50.0, "REF-002")
        status = get_payment_status(result["payment_id"])
        assert status is not None
        assert status["status"] == "pending_mock"


class TestPaymentToolCalls:
    def test_list_accounts(self):
        result = handle_tool_call("list_accounts", {})
        assert result["count"] == 2

    def test_get_balance(self):
        result = handle_tool_call("get_balance", {"account_id": "acc_001"})
        assert result["balance"] == 125000.00

    def test_get_balance_not_found(self):
        result = handle_tool_call("get_balance", {"account_id": "nonexistent"})
        assert "error" in result

    def test_list_transactions(self):
        result = handle_tool_call("list_transactions", {})
        assert result["count"] == 4

    def test_list_transactions_filtered(self):
        result = handle_tool_call("list_transactions", {"account_id": "acc_002"})
        assert result["count"] == 1

    def test_initiate_payment_dry_run(self):
        result = handle_tool_call("initiate_payment", {
            "from_account": "acc_001",
            "to_name": "Vendor",
            "to_iban": "AE999",
            "amount": 200.0,
            "reference": "TEST",
        })
        assert result["status"] == "dry_run"

    def test_unknown_tool(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            handle_tool_call("nonexistent", {})


class TestPaymentMCPProtocol:
    def test_initialize(self):
        response = handle_request({
            "jsonrpc": "2.0", "method": "initialize", "id": 1
        })
        assert response["result"]["serverInfo"]["name"] == "ai-employee-payment"

    def test_tools_list(self):
        response = handle_request({
            "jsonrpc": "2.0", "method": "tools/list", "id": 1
        })
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "list_accounts" in tool_names
        assert "get_balance" in tool_names
        assert "initiate_payment" in tool_names
        assert "payment_status" in tool_names
        assert len(tools) == 5

    def test_tools_call_list_accounts(self):
        response = handle_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "list_accounts", "arguments": {}},
        })
        content = response["result"]["content"]
        data = json.loads(content[0]["text"])
        assert data["count"] == 2

    def test_tools_call_get_balance(self):
        response = handle_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "get_balance", "arguments": {"account_id": "acc_002"}},
        })
        content = response["result"]["content"]
        data = json.loads(content[0]["text"])
        assert data["balance"] == 350000.00

    def test_unknown_method(self):
        response = handle_request({
            "jsonrpc": "2.0", "method": "nonexistent", "id": 1
        })
        assert "error" in response

    def test_unknown_tool_call(self):
        response = handle_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "bad_tool", "arguments": {}},
        })
        assert "error" in response
