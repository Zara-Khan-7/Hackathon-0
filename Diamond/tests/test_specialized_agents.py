"""Tests for specialized Diamond agents."""

import pytest
from src.agents.base_agent import BaseSpecializedAgent, AgentStatus, AgentCapability
from src.agents.sales_agent import SalesAgent
from src.agents.finance_agent import FinanceAgent
from src.agents.content_agent import ContentAgent
from src.agents.security_agent import SecurityAgent


class TestBaseAgent:
    def test_default_attributes(self):
        agent = BaseSpecializedAgent()
        assert agent.AGENT_TYPE == "base"
        assert agent.status == AgentStatus.IDLE
        assert agent._tasks_completed == 0

    def test_custom_agent_id(self):
        agent = BaseSpecializedAgent(agent_id="test-001")
        assert agent.agent_id == "test-001"

    def test_get_stats(self):
        agent = BaseSpecializedAgent()
        stats = agent.get_stats()
        assert stats["type"] == "base"
        assert stats["status"] == "idle"
        assert stats["tasks_completed"] == 0

    def test_process_task(self):
        agent = BaseSpecializedAgent()
        result = agent.process_task({"filename": "TEST_001.md"})
        assert result["status"] == "success"
        assert agent._tasks_completed == 1

    def test_process_task_dry_run(self):
        agent = BaseSpecializedAgent()
        result = agent.process_task({"filename": "TEST_001.md"}, dry_run=True)
        assert result["status"] == "success"

    def test_status_returns_to_idle_after_task(self):
        agent = BaseSpecializedAgent()
        agent.process_task({"filename": "TEST_001.md"})
        assert agent.status == AgentStatus.IDLE

    def test_repr(self):
        agent = BaseSpecializedAgent(agent_id="test-001")
        assert "test-001" in repr(agent)


class TestSalesAgent:
    def test_agent_type(self):
        agent = SalesAgent()
        assert agent.AGENT_TYPE == "sales"
        assert agent.DISPLAY_NAME == "Sales Agent"

    def test_handles_email(self):
        agent = SalesAgent()
        assert agent.can_handle("EMAIL_")

    def test_handles_linkedin(self):
        agent = SalesAgent()
        assert agent.can_handle("LINKEDIN_")

    def test_handles_salespost(self):
        agent = SalesAgent()
        assert agent.can_handle("SALESPOST_")

    def test_does_not_handle_payment(self):
        agent = SalesAgent()
        assert not agent.can_handle("PAYMENT_")

    def test_score_email_task(self):
        agent = SalesAgent()
        task = {"filename": "EMAIL_test.md"}
        assert agent.score_task(task) > 0

    def test_process_email(self):
        agent = SalesAgent()
        task = {
            "filename": "EMAIL_mock_001.md",
            "task_type": "email",
            "body": "Test email",
            "metadata": {"from": "alice@test.com", "subject": "Hello"},
        }
        result = agent.process_task(task)
        assert result["status"] == "success"
        assert "alice@test.com" in result["result"]

    def test_process_linkedin(self):
        agent = SalesAgent()
        task = {"filename": "LINKEDIN_001.md", "task_type": "linkedin", "body": ""}
        result = agent.process_task(task)
        assert result["status"] == "success"

    def test_process_dry_run(self):
        agent = SalesAgent()
        task = {"filename": "EMAIL_001.md", "task_type": "email", "body": ""}
        result = agent.process_task(task, dry_run=True)
        assert "DRY-RUN" in result["result"]


class TestFinanceAgent:
    def test_agent_type(self):
        agent = FinanceAgent()
        assert agent.AGENT_TYPE == "finance"

    def test_handles_odoo(self):
        agent = FinanceAgent()
        assert agent.can_handle("ODOO_")

    def test_handles_payment(self):
        agent = FinanceAgent()
        assert agent.can_handle("PAYMENT_")

    def test_handles_audit(self):
        agent = FinanceAgent()
        assert agent.can_handle("AUDIT_")

    def test_does_not_handle_email(self):
        agent = FinanceAgent()
        assert not agent.can_handle("EMAIL_")

    def test_process_odoo(self):
        agent = FinanceAgent()
        task = {
            "filename": "ODOO_sync_001.md",
            "task_type": "odoo",
            "body": "",
            "metadata": {"subtype": "invoice"},
        }
        result = agent.process_task(task)
        assert result["status"] == "success"

    def test_process_payment(self):
        agent = FinanceAgent()
        task = {
            "filename": "PAYMENT_vendor_001.md",
            "task_type": "payment",
            "body": "",
            "metadata": {"amount": "500"},
        }
        result = agent.process_task(task)
        assert result["status"] == "success"
        assert "approval" in result["result"].lower()


class TestContentAgent:
    def test_agent_type(self):
        agent = ContentAgent()
        assert agent.AGENT_TYPE == "content"

    def test_handles_all_social(self):
        agent = ContentAgent()
        assert agent.can_handle("FACEBOOK_")
        assert agent.can_handle("INSTAGRAM_")
        assert agent.can_handle("TWITTER_")
        assert agent.can_handle("SOCIAL_")

    def test_handles_whatsapp(self):
        agent = ContentAgent()
        assert agent.can_handle("WHATSAPP_")

    def test_does_not_handle_odoo(self):
        agent = ContentAgent()
        assert not agent.can_handle("ODOO_")

    def test_process_facebook(self):
        agent = ContentAgent()
        task = {"filename": "FACEBOOK_post_001.md", "task_type": "facebook", "body": ""}
        result = agent.process_task(task)
        assert result["status"] == "success"
        assert "Facebook" in result["result"]

    def test_process_whatsapp(self):
        agent = ContentAgent()
        task = {
            "filename": "WHATSAPP_reply_001.md",
            "task_type": "whatsapp",
            "body": "",
            "metadata": {"from": "John"},
        }
        result = agent.process_task(task)
        assert result["status"] == "success"


class TestSecurityAgent:
    def test_agent_type(self):
        agent = SecurityAgent()
        assert agent.AGENT_TYPE == "security"

    def test_handles_error(self):
        agent = SecurityAgent()
        assert agent.can_handle("ERROR_")

    def test_handles_execute(self):
        agent = SecurityAgent()
        assert agent.can_handle("EXECUTE_")

    def test_scan_clean_content(self):
        agent = SecurityAgent()
        scan = agent.scan_outgoing("Hello world, let's schedule a meeting", "email")
        assert scan["passed"] is True
        assert len(scan["issues"]) == 0

    def test_scan_sensitive_content(self):
        agent = SecurityAgent()
        scan = agent.scan_outgoing("Here is the password: abc123", "email")
        assert scan["passed"] is False
        assert len(scan["issues"]) > 0

    def test_investigate_error_clean(self):
        agent = SecurityAgent()
        task = {"filename": "ERROR_001.md", "body": "Connection timeout"}
        result = agent.process_task(task)
        assert result["status"] == "success"
        assert "no security" in result["result"].lower()

    def test_investigate_error_sensitive(self):
        agent = SecurityAgent()
        task = {"filename": "ERROR_001.md", "body": "Failed to read token from vault"}
        result = agent.process_task(task)
        assert result["status"] == "success"
        assert "SECURITY ALERT" in result["result"]

    def test_validate_execution(self):
        agent = SecurityAgent()
        task = {"filename": "EXECUTE_001.md", "body": "Send email to client"}
        result = agent.process_task(task)
        assert result["status"] == "success"
        assert "validated" in result["result"].lower()
