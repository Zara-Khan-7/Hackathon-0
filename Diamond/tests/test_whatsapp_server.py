"""Tests for src.mcp_whatsapp — WhatsApp MCP server and mock data."""

import json
import pytest

from src.mcp_whatsapp.mock_whatsapp import get_chats, get_messages, send_message, MOCK_SENT
from src.mcp_whatsapp.whatsapp_server import handle_request, handle_tool_call


class TestMockWhatsApp:
    def test_get_chats(self):
        chats = get_chats()
        assert len(chats) == 3
        assert all("chat_id" in c for c in chats)
        assert all("name" in c for c in chats)

    def test_get_messages(self):
        msgs = get_messages("wa_chat_001")
        assert len(msgs) > 0
        assert all("text" in m for m in msgs)

    def test_get_messages_unknown_chat(self):
        msgs = get_messages("nonexistent")
        assert msgs == []

    def test_send_message(self):
        before = len(MOCK_SENT)
        result = send_message("wa_chat_001", "Test message")
        assert result["status"] == "sent_mock"
        assert len(MOCK_SENT) == before + 1


class TestWhatsAppToolCalls:
    def test_list_chats(self):
        result = handle_tool_call("list_whatsapp_chats", {})
        assert "chats" in result
        assert result["count"] == 3

    def test_read_chat(self):
        result = handle_tool_call("read_whatsapp_chat", {"chat_id": "wa_chat_001"})
        assert "messages" in result
        assert result["count"] > 0

    def test_read_chat_not_found(self):
        result = handle_tool_call("read_whatsapp_chat", {"chat_id": "nonexistent"})
        assert "error" in result

    def test_send_dry_run(self):
        result = handle_tool_call("send_whatsapp", {
            "chat_id": "wa_chat_001",
            "message": "Hello from test",
        })
        assert result["status"] == "dry_run"

    def test_unknown_tool(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            handle_tool_call("nonexistent_tool", {})


class TestWhatsAppMCPProtocol:
    def test_initialize(self):
        response = handle_request({
            "jsonrpc": "2.0", "method": "initialize", "id": 1
        })
        assert response["result"]["serverInfo"]["name"] == "ai-employee-whatsapp"

    def test_tools_list(self):
        response = handle_request({
            "jsonrpc": "2.0", "method": "tools/list", "id": 1
        })
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "list_whatsapp_chats" in tool_names
        assert "read_whatsapp_chat" in tool_names
        assert "send_whatsapp" in tool_names

    def test_tools_call_list_chats(self):
        response = handle_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "list_whatsapp_chats", "arguments": {}},
        })
        content = response["result"]["content"]
        assert len(content) > 0
        data = json.loads(content[0]["text"])
        assert data["count"] == 3

    def test_tools_call_send_whatsapp(self):
        response = handle_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "send_whatsapp",
                "arguments": {"chat_id": "wa_chat_001", "message": "Test"},
            },
        })
        content = response["result"]["content"]
        data = json.loads(content[0]["text"])
        assert data["status"] == "dry_run"

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
