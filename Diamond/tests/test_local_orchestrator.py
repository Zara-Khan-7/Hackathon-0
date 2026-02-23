"""Tests for src.orchestrator.local_orchestrator — full-access local agent."""

import pytest
from pathlib import Path

from src.config.agent_config import AgentConfig, AgentRole
from src.orchestrator.local_orchestrator import LocalOrchestrator


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Set up a temporary project structure."""
    monkeypatch.setattr("src.utils.file_ops.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("src.claim.claim_manager.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("src.health.heartbeat.get_project_root", lambda: tmp_path)

    for folder in ["Needs_Action", "In_Progress", "Pending_Approval", "Done", "Logs", "Errors"]:
        (tmp_path / folder).mkdir()

    return tmp_path


@pytest.fixture
def local_orch(tmp_project, monkeypatch):
    """Create a LocalOrchestrator in dry-run mode."""
    monkeypatch.setenv("AGENT_ID", "local-test")
    monkeypatch.setenv("AGENT_ROLE", "local")
    monkeypatch.setenv("GIT_SYNC_ENABLED", "false")
    config = AgentConfig()
    return LocalOrchestrator(config=config, dry_run=True)


class TestLocalOrchestrator:
    def test_role_is_local(self, local_orch):
        assert local_orch.config.role == AgentRole.LOCAL

    def test_agent_id(self, local_orch):
        assert local_orch.agent_id == "local-test"

    def test_poll_empty_returns_zero(self, local_orch):
        result = local_orch.poll_once()
        assert result == 0

    def test_handles_whatsapp_task(self, tmp_project, local_orch):
        task = tmp_project / "Needs_Action" / "WHATSAPP_chat_001.md"
        task.write_text("---\ntype: whatsapp\npriority: medium\n---\nNew message\n")

        result = local_orch.poll_once()
        assert result == 1
        assert not task.exists()

    def test_handles_payment_task(self, tmp_project, local_orch):
        task = tmp_project / "Needs_Action" / "PAYMENT_transfer_001.md"
        task.write_text("---\ntype: payment\npriority: high\n---\nTransfer request\n")

        result = local_orch.poll_once()
        assert result == 1
        assert not task.exists()

    def test_handles_execute_task(self, tmp_project, local_orch):
        task = tmp_project / "Needs_Action" / "EXECUTE_EMAIL_001.md"
        task.write_text("---\ntype: execute\npriority: high\n---\nApproved action\n")

        result = local_orch.poll_once()
        assert result == 1
        assert not task.exists()

    def test_extended_skill_routing(self, local_orch):
        assert local_orch._get_skill_for_type("whatsapp") == "whatsapp_reply"
        assert local_orch._get_skill_for_type("payment") == "process_payment"
        # Gold skills still work
        assert local_orch._get_skill_for_type("email") == "complete_task"

    def test_writes_heartbeat(self, tmp_project, local_orch):
        local_orch.poll_once()
        heartbeat = tmp_project / ".heartbeat_local-test.json"
        assert heartbeat.exists()

    def test_classify_whatsapp(self, tmp_project, local_orch):
        task = tmp_project / "Needs_Action" / "WHATSAPP_chat_001.md"
        task.write_text("---\ntype: unknown\n---\nTest\n")
        classified = local_orch._classify_task(task)
        assert classified["task_type"] == "whatsapp"

    def test_classify_payment(self, tmp_project, local_orch):
        task = tmp_project / "Needs_Action" / "PAYMENT_tx_001.md"
        task.write_text("---\ntype: unknown\n---\nTest\n")
        classified = local_orch._classify_task(task)
        assert classified["task_type"] == "payment"
