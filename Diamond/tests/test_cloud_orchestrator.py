"""Tests for src.orchestrator.cloud_orchestrator — draft-only cloud agent."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.agent_config import AgentConfig, AgentRole
from src.orchestrator.cloud_orchestrator import CloudOrchestrator


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
def cloud_orch(tmp_project, monkeypatch):
    """Create a CloudOrchestrator in dry-run mode."""
    monkeypatch.setenv("AGENT_ID", "cloud-test")
    monkeypatch.setenv("AGENT_ROLE", "cloud")
    monkeypatch.setenv("GIT_SYNC_ENABLED", "false")
    config = AgentConfig()
    return CloudOrchestrator(config=config, dry_run=True)


class TestCloudOrchestrator:
    def test_role_is_cloud(self, cloud_orch):
        assert cloud_orch.config.role == AgentRole.CLOUD

    def test_agent_id(self, cloud_orch):
        assert cloud_orch.agent_id == "cloud-test"

    def test_poll_empty_returns_zero(self, cloud_orch):
        result = cloud_orch.poll_once()
        assert result == 0

    def test_skips_whatsapp_task(self, tmp_project, cloud_orch):
        # Create a WHATSAPP_ task
        task = tmp_project / "Needs_Action" / "WHATSAPP_chat_001.md"
        task.write_text("---\ntype: whatsapp\n---\nTest\n")

        result = cloud_orch.poll_once()
        # Cloud should skip WHATSAPP_ tasks
        assert result == 0
        # File should remain in Needs_Action
        assert task.exists()

    def test_skips_payment_task(self, tmp_project, cloud_orch):
        task = tmp_project / "Needs_Action" / "PAYMENT_transfer_001.md"
        task.write_text("---\ntype: payment\n---\nTest\n")

        result = cloud_orch.poll_once()
        assert result == 0
        assert task.exists()

    def test_skips_execute_task(self, tmp_project, cloud_orch):
        task = tmp_project / "Needs_Action" / "EXECUTE_EMAIL_001.md"
        task.write_text("---\ntype: execute\n---\nTest\n")

        result = cloud_orch.poll_once()
        assert result == 0
        assert task.exists()

    def test_processes_email_as_draft(self, tmp_project, cloud_orch):
        task = tmp_project / "Needs_Action" / "EMAIL_mock_001.md"
        task.write_text("---\ntype: email\npriority: medium\nrequires_approval: true\n---\nReply to customer\n")

        result = cloud_orch.poll_once()
        assert result == 1
        # Task should be moved from Needs_Action
        assert not task.exists()

    def test_processes_schedule_fully(self, tmp_project, cloud_orch):
        task = tmp_project / "Needs_Action" / "SCHEDULE_scan.md"
        task.write_text("---\ntype: schedule\npriority: low\nrequires_approval: false\n---\nDaily scan\n")

        result = cloud_orch.poll_once()
        assert result == 1
        assert not task.exists()

    def test_writes_heartbeat(self, tmp_project, cloud_orch):
        cloud_orch.poll_once()
        heartbeat = tmp_project / ".heartbeat_cloud-test.json"
        assert heartbeat.exists()

    def test_claims_before_processing(self, tmp_project, cloud_orch):
        task = tmp_project / "Needs_Action" / "AUDIT_weekly.md"
        task.write_text("---\ntype: audit\npriority: low\n---\nWeekly audit\n")

        cloud_orch.poll_once()
        # After processing, task should no longer be in Needs_Action
        assert not task.exists()
