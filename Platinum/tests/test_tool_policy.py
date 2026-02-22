"""Tests for src.config.tool_policy — MCP tool safety classification."""

import pytest

from src.config.agent_config import AgentRole
from src.config.tool_policy import (
    get_classification,
    is_allowed,
    get_blocked_tools,
    get_allowed_tools,
    is_local_only_server,
    SAFE,
    DRAFT,
    DANGEROUS,
)


class TestGetClassification:
    def test_safe_tools(self):
        assert get_classification("list_drafts") == SAFE
        assert get_classification("list_invoices") == SAFE
        assert get_classification("get_social_summary") == SAFE
        assert get_classification("list_whatsapp_chats") == SAFE
        assert get_classification("get_balance") == SAFE

    def test_draft_tools(self):
        assert get_classification("draft_email") == DRAFT
        assert get_classification("create_invoice_draft") == DRAFT
        assert get_classification("draft_social_post") == DRAFT

    def test_dangerous_tools(self):
        assert get_classification("send_email") == DANGEROUS
        assert get_classification("post_invoice") == DANGEROUS
        assert get_classification("post_facebook") == DANGEROUS
        assert get_classification("send_whatsapp") == DANGEROUS
        assert get_classification("initiate_payment") == DANGEROUS

    def test_unknown_tool_defaults_dangerous(self):
        assert get_classification("some_random_tool") == DANGEROUS


class TestIsAllowed:
    def test_local_allows_everything(self):
        assert is_allowed("send_email", AgentRole.LOCAL) is True
        assert is_allowed("initiate_payment", AgentRole.LOCAL) is True
        assert is_allowed("post_facebook", AgentRole.LOCAL) is True

    def test_gold_allows_everything(self):
        assert is_allowed("send_email", AgentRole.GOLD) is True
        assert is_allowed("initiate_payment", AgentRole.GOLD) is True

    def test_cloud_allows_safe(self):
        assert is_allowed("list_drafts", AgentRole.CLOUD) is True
        assert is_allowed("list_invoices", AgentRole.CLOUD) is True

    def test_cloud_allows_draft(self):
        assert is_allowed("draft_email", AgentRole.CLOUD) is True
        assert is_allowed("create_invoice_draft", AgentRole.CLOUD) is True

    def test_cloud_blocks_dangerous(self):
        assert is_allowed("send_email", AgentRole.CLOUD) is False
        assert is_allowed("post_invoice", AgentRole.CLOUD) is False
        assert is_allowed("send_whatsapp", AgentRole.CLOUD) is False
        assert is_allowed("initiate_payment", AgentRole.CLOUD) is False


class TestGetBlockedTools:
    def test_cloud_blocked_list(self):
        blocked = get_blocked_tools(AgentRole.CLOUD)
        assert "send_email" in blocked
        assert "post_invoice" in blocked
        assert "initiate_payment" in blocked
        assert "list_drafts" not in blocked

    def test_local_blocks_nothing(self):
        blocked = get_blocked_tools(AgentRole.LOCAL)
        assert len(blocked) == 0


class TestGetAllowedTools:
    def test_cloud_allowed_list(self):
        allowed = get_allowed_tools(AgentRole.CLOUD)
        assert "list_drafts" in allowed
        assert "draft_email" in allowed
        assert "send_email" not in allowed

    def test_local_allows_all(self):
        from src.config.tool_policy import TOOL_POLICY
        allowed = get_allowed_tools(AgentRole.LOCAL)
        assert len(allowed) == len(TOOL_POLICY)


class TestIsLocalOnlyServer:
    def test_whatsapp_local_only(self):
        assert is_local_only_server("whatsapp") is True

    def test_payment_local_only(self):
        assert is_local_only_server("payment") is True

    def test_email_not_local_only(self):
        assert is_local_only_server("email") is False

    def test_odoo_not_local_only(self):
        assert is_local_only_server("odoo") is False
