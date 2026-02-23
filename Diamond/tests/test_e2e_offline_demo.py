"""End-to-end offline demo — simulates cloud→local handoff with mock data.

Tests the full Platinum tier pipeline:
1. Cloud watcher creates task
2. Cloud orchestrator drafts → Pending_Approval
3. Local picks up approval → creates EXECUTE_
4. Local orchestrator executes → Done
5. Health monitor reports healthy
"""

import json
import pytest
from pathlib import Path

from src.config.agent_config import AgentConfig, AgentRole
from src.config.domain_router import should_handle, get_cloud_action, CLOUD_ACTION_DRAFT, CLOUD_ACTION_SKIP
from src.config.tool_policy import is_allowed, get_classification, SAFE, DRAFT, DANGEROUS
from src.claim.claim_manager import ClaimManager
from src.sync.git_sync import GitVaultSync
from src.health.heartbeat import write_heartbeat, read_heartbeat
from src.health.health_monitor import HealthMonitor
from src.utils.file_ops import get_folder, create_task_file, list_md_files, safe_move


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Set up a complete project structure for e2e testing."""
    monkeypatch.setattr("src.utils.file_ops.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("src.claim.claim_manager.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("src.health.heartbeat.get_project_root", lambda: tmp_path)

    for folder in [
        "Inbox", "Needs_Action", "In_Progress", "Pending_Approval",
        "Approved", "Rejected", "Done", "Logs", "Errors",
        "Accounting", "Briefings",
    ]:
        (tmp_path / folder).mkdir()

    return tmp_path


class TestE2ECloudToLocal:
    """Simulate the full cloud→local handoff flow."""

    def test_step1_cloud_watcher_creates_email_task(self, tmp_project):
        """Step 1: A watcher detects an email and creates a task."""
        metadata = {
            "type": "email",
            "priority": "medium",
            "requires_approval": True,
            "from": "customer@example.com",
            "subject": "Invoice request",
        }
        body = "Please send me invoice #101 for last month's services."

        task_path = create_task_file("Needs_Action", "EMAIL", "mock_email_001", metadata, body)
        assert task_path.exists()
        assert task_path.name == "EMAIL_mock_email_001.md"

    def test_step2_cloud_routes_email_as_draft(self, tmp_project):
        """Step 2: Cloud orchestrator sees EMAIL_ → draft_only action."""
        assert get_cloud_action("EMAIL_mock_email_001.md") == CLOUD_ACTION_DRAFT
        assert should_handle("EMAIL_mock_email_001.md", AgentRole.CLOUD) is True

    def test_step3_cloud_claims_and_creates_approval(self, tmp_project):
        """Step 3: Cloud claims the task and creates approval request."""
        # Create task
        task_path = create_task_file(
            "Needs_Action", "EMAIL", "mock_001",
            {"type": "email", "priority": "medium", "requires_approval": True},
            "Reply to customer about invoice",
        )

        # Cloud claims it
        cloud_cm = ClaimManager("cloud-001")
        claimed = cloud_cm.claim(task_path)
        assert claimed is not None
        assert not task_path.exists()

        # Cloud creates approval file (simulating draft)
        approval_path = create_task_file(
            "Pending_Approval", "APPROVE", "EMAIL_mock_001",
            {"type": "approval", "original_task": "EMAIL_mock_001.md", "priority": "medium"},
            "# Draft Reply\n\nDear Customer,\nPlease find attached invoice #101.\n",
        )
        assert approval_path.exists()

        # Move claimed file to Done (cloud is done with it)
        safe_move(claimed, "Done")

    def test_step4_cloud_pushes_git(self, tmp_project):
        """Step 4: Cloud syncs via git (mock)."""
        sync = GitVaultSync("cloud-001")
        result = sync.push(message="[cloud-001] Created approval for EMAIL_mock_001")
        assert result["status"] == "success"

    def test_step5_local_pulls_and_sees_approval(self, tmp_project):
        """Step 5: Local pulls and finds approval in Pending_Approval/."""
        sync = GitVaultSync("local-001")
        result = sync.pull()
        assert result["status"] == "success"

        # Simulate: approval file exists after pull
        create_task_file(
            "Pending_Approval", "APPROVE", "EMAIL_mock_001",
            {"type": "approval", "priority": "medium"},
            "Draft reply content",
        )

        approvals = list_md_files("Pending_Approval")
        assert len(approvals) >= 1

    def test_step6_local_approves_creates_execute(self, tmp_project):
        """Step 6: User approves → EXECUTE_ file created."""
        # Create the approval
        approval = create_task_file(
            "Pending_Approval", "APPROVE", "EMAIL_mock_001",
            {"type": "approval", "priority": "medium"},
            "Draft reply",
        )

        # Approve → create EXECUTE_
        execute_path = create_task_file(
            "Needs_Action", "EXECUTE", "EMAIL_mock_001",
            {"type": "execute", "priority": "high", "approved_by": "human"},
            "Approved: send the reply to customer@example.com",
        )
        assert execute_path.exists()

        # Move approval to Approved
        safe_move(approval, "Approved")

    def test_step7_local_executes_and_completes(self, tmp_project):
        """Step 7: Local orchestrator executes and moves to Done."""
        execute = create_task_file(
            "Needs_Action", "EXECUTE", "EMAIL_mock_001",
            {"type": "execute", "priority": "high"},
            "Send email to customer",
        )

        local_cm = ClaimManager("local-001")
        claimed = local_cm.claim(execute)
        assert claimed is not None

        # Simulate execution (dry-run would happen here)
        safe_move(claimed, "Done")

        done_files = list_md_files("Done")
        done_names = [f.name for f in done_files]
        assert any("EXECUTE" in n for n in done_names)


class TestE2ECloudSkipsLocalOnly:
    """Verify cloud correctly skips local-only tasks."""

    def test_cloud_skips_whatsapp(self, tmp_project):
        task = create_task_file(
            "Needs_Action", "WHATSAPP", "chat_001",
            {"type": "whatsapp"}, "New message"
        )
        assert should_handle(task.name, AgentRole.CLOUD) is False
        assert should_handle(task.name, AgentRole.LOCAL) is True

    def test_cloud_skips_payment(self, tmp_project):
        task = create_task_file(
            "Needs_Action", "PAYMENT", "transfer_001",
            {"type": "payment"}, "Transfer request"
        )
        assert should_handle(task.name, AgentRole.CLOUD) is False
        assert should_handle(task.name, AgentRole.LOCAL) is True


class TestE2EToolPolicyEnforcement:
    """Verify tool policy blocks dangerous tools on cloud."""

    def test_cloud_cannot_send_email(self):
        assert is_allowed("send_email", AgentRole.CLOUD) is False

    def test_cloud_can_draft_email(self):
        assert is_allowed("draft_email", AgentRole.CLOUD) is True

    def test_cloud_cannot_initiate_payment(self):
        assert is_allowed("initiate_payment", AgentRole.CLOUD) is False

    def test_local_can_do_everything(self):
        assert is_allowed("send_email", AgentRole.LOCAL) is True
        assert is_allowed("initiate_payment", AgentRole.LOCAL) is True
        assert is_allowed("send_whatsapp", AgentRole.LOCAL) is True


class TestE2EHealthMonitoring:
    """Verify health monitoring works end-to-end."""

    def test_both_agents_healthy(self, tmp_project):
        write_heartbeat("cloud-001")
        write_heartbeat("local-001")

        monitor = HealthMonitor()
        report = monitor.run_all_checks(["cloud-001", "local-001"])
        assert report["overall_status"] == "healthy"

    def test_alert_when_agent_missing(self, tmp_project):
        write_heartbeat("local-001")
        # cloud-001 has NO heartbeat

        monitor = HealthMonitor()
        report = monitor.run_all_checks(["cloud-001", "local-001"])
        assert report["overall_status"] == "degraded"

        # Should create alert
        alerts = list_md_files("Needs_Action")
        alert_names = [f.name for f in alerts]
        assert any("ERROR" in n for n in alert_names)


class TestE2EClaimSystem:
    """Verify claim-by-move prevents double processing."""

    def test_two_agents_cannot_claim_same_task(self, tmp_project):
        task = create_task_file(
            "Needs_Action", "EMAIL", "shared_001",
            {"type": "email"}, "Test task"
        )

        cloud_cm = ClaimManager("cloud-001")
        local_cm = ClaimManager("local-001")

        # First claim succeeds
        result1 = cloud_cm.claim(task)
        assert result1 is not None

        # Second claim fails (file already moved)
        result2 = local_cm.claim(task)
        assert result2 is None

    def test_stale_claims_get_cleaned_up(self, tmp_project):
        import os, time as t

        # Create a stale claim
        agent_folder = tmp_project / "In_Progress" / "dead-agent"
        agent_folder.mkdir(parents=True)
        stale = agent_folder / "STALE_task_001.md"
        stale.write_text("stale\n")
        old_time = t.time() - 7200
        os.utime(str(stale), (old_time, old_time))

        cm = ClaimManager("cleanup-agent")
        moved = cm.cleanup_stale(max_age_seconds=3600)
        assert len(moved) == 1
        assert (tmp_project / "Needs_Action" / "STALE_task_001.md").exists()
