"""Tests for src.config.domain_router — routing rules and prefix matching."""

import pytest

from src.config.agent_config import AgentRole
from src.config.domain_router import (
    get_prefix,
    should_handle,
    get_cloud_action,
    get_routing_reason,
    list_skipped_prefixes,
    CLOUD_ACTION_DRAFT,
    CLOUD_ACTION_FULL,
    CLOUD_ACTION_SKIP,
)


class TestGetPrefix:
    def test_email_prefix(self):
        assert get_prefix("EMAIL_mock_001.md") == "EMAIL_"

    def test_whatsapp_prefix(self):
        assert get_prefix("WHATSAPP_chat_001.md") == "WHATSAPP_"

    def test_payment_prefix(self):
        assert get_prefix("PAYMENT_transfer_001.md") == "PAYMENT_"

    def test_execute_prefix(self):
        assert get_prefix("EXECUTE_EMAIL_mock_001.md") == "EXECUTE_"

    def test_unknown_prefix(self):
        assert get_prefix("RANDOM_task.md") is None


class TestShouldHandle:
    def test_gold_handles_everything(self):
        assert should_handle("EMAIL_mock.md", AgentRole.GOLD) is True
        assert should_handle("WHATSAPP_chat.md", AgentRole.GOLD) is True
        assert should_handle("PAYMENT_tx.md", AgentRole.GOLD) is True
        assert should_handle("EXECUTE_foo.md", AgentRole.GOLD) is True

    def test_cloud_handles_email(self):
        assert should_handle("EMAIL_mock.md", AgentRole.CLOUD) is True

    def test_cloud_skips_whatsapp(self):
        assert should_handle("WHATSAPP_chat.md", AgentRole.CLOUD) is False

    def test_cloud_skips_payment(self):
        assert should_handle("PAYMENT_tx.md", AgentRole.CLOUD) is False

    def test_cloud_skips_execute(self):
        assert should_handle("EXECUTE_foo.md", AgentRole.CLOUD) is False

    def test_cloud_skips_approve(self):
        assert should_handle("APPROVE_foo.md", AgentRole.CLOUD) is False

    def test_cloud_handles_schedule(self):
        assert should_handle("SCHEDULE_scan.md", AgentRole.CLOUD) is True

    def test_cloud_handles_audit(self):
        assert should_handle("AUDIT_weekly.md", AgentRole.CLOUD) is True

    def test_local_handles_all(self):
        for prefix in ["EMAIL_", "WHATSAPP_", "PAYMENT_", "EXECUTE_", "APPROVE_"]:
            assert should_handle(f"{prefix}test.md", AgentRole.LOCAL) is True


class TestGetCloudAction:
    def test_email_is_draft(self):
        assert get_cloud_action("EMAIL_mock.md") == CLOUD_ACTION_DRAFT

    def test_whatsapp_is_skip(self):
        assert get_cloud_action("WHATSAPP_chat.md") == CLOUD_ACTION_SKIP

    def test_schedule_is_full(self):
        assert get_cloud_action("SCHEDULE_scan.md") == CLOUD_ACTION_FULL

    def test_odoo_is_draft(self):
        assert get_cloud_action("ODOO_invoice.md") == CLOUD_ACTION_DRAFT

    def test_unknown_defaults_to_draft(self):
        assert get_cloud_action("RANDOM_task.md") == CLOUD_ACTION_DRAFT


class TestGetRoutingReason:
    def test_email_reason(self):
        reason = get_routing_reason("EMAIL_mock.md")
        assert "local" in reason.lower() or "smtp" in reason.lower()

    def test_unknown_reason(self):
        reason = get_routing_reason("RANDOM_task.md")
        assert "unknown" in reason.lower() or "default" in reason.lower()


class TestListSkippedPrefixes:
    def test_cloud_skipped(self):
        skipped = list_skipped_prefixes(AgentRole.CLOUD)
        assert "WHATSAPP_" in skipped
        assert "PAYMENT_" in skipped
        assert "EXECUTE_" in skipped
        assert "APPROVE_" in skipped

    def test_local_skips_nothing(self):
        skipped = list_skipped_prefixes(AgentRole.LOCAL)
        assert len(skipped) == 0
