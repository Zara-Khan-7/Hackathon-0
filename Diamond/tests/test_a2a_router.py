"""Tests for A2A message router."""

import pytest
from src.a2a.message_bus import MockMessageBus
from src.a2a.router import MessageRouter
from src.agents.agent_registry import create_default_registry


@pytest.fixture
def router():
    bus = MockMessageBus()
    registry = create_default_registry()
    return MessageRouter(bus, registry)


class TestMessageRouter:
    def test_delegate_task_auto(self, router):
        task = {"filename": "EMAIL_test.md", "task_type": "email",
                "priority": "medium", "body": ""}
        msg = router.delegate_task("orchestrator", task)
        assert msg is not None
        assert msg.recipient_id == "sales-agent"

    def test_delegate_task_specific(self, router):
        task = {"filename": "EMAIL_test.md", "task_type": "email", "priority": "medium"}
        msg = router.delegate_task("orchestrator", task, target_agent_id="finance-agent")
        assert msg is not None
        assert msg.recipient_id == "finance-agent"

    def test_delegate_no_matching_agent(self, router):
        task = {"filename": "UNKNOWN_test.md", "task_type": "unknown", "priority": "medium"}
        msg = router.delegate_task("orchestrator", task)
        assert msg is None

    def test_send_result(self, router):
        msg = router.send_result("sales-agent", "orchestrator",
                                 {"status": "done"}, correlation_id="abc")
        assert msg.correlation_id == "abc"
        messages = router.get_messages("orchestrator")
        assert len(messages) == 1

    def test_request_info(self, router):
        msg = router.request_info("sales-agent", "finance-agent", "What is balance?")
        assert msg is not None
        messages = router.get_messages("finance-agent")
        assert len(messages) == 1
        assert messages[0].payload["query"] == "What is balance?"

    def test_respond_info(self, router):
        msg = router.respond_info("finance-agent", "sales-agent", {"balance": 50000})
        messages = router.get_messages("sales-agent")
        assert len(messages) == 1

    def test_broadcast_alert(self, router):
        msg = router.broadcast_alert("security-agent", "credential_leak",
                                     {"file": "test.md"})
        assert msg.is_broadcast

    def test_broadcast_status(self, router):
        msg = router.broadcast_status("sales-agent", "idle")
        assert msg.is_broadcast

    def test_pending_count(self, router):
        task = {"filename": "EMAIL_test.md", "task_type": "email", "priority": "medium"}
        router.delegate_task("orchestrator", task)
        assert router.pending_count("sales-agent") == 1

    def test_get_stats(self, router):
        stats = router.get_stats()
        assert "bus" in stats
        assert "registry" in stats
        assert stats["registry"]["total_agents"] == 4

    def test_finance_task_routes_to_finance(self, router):
        task = {"filename": "PAYMENT_vendor.md", "task_type": "payment", "priority": "high"}
        msg = router.delegate_task("orchestrator", task)
        assert msg is not None
        assert msg.recipient_id == "finance-agent"

    def test_content_task_routes_to_content(self, router):
        task = {"filename": "FACEBOOK_post.md", "task_type": "facebook", "priority": "medium"}
        msg = router.delegate_task("orchestrator", task)
        assert msg is not None
        assert msg.recipient_id == "content-agent"
