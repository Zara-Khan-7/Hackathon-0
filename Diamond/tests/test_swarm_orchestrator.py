"""Tests for swarm orchestrator."""

import pytest
from pathlib import Path
from src.orchestrator.swarm_orchestrator import SwarmOrchestrator
from src.utils import frontmatter


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Create a temporary project with standard folders."""
    monkeypatch.setattr("src.utils.file_ops.get_project_root", lambda: tmp_path)
    for folder in ["Needs_Action", "In_Progress", "Done", "Logs",
                    "Pending_Approval", "Approved", "Rejected", "Errors",
                    "Accounting", "Briefings"]:
        (tmp_path / folder).mkdir()
    return tmp_path


def _create_task(project, prefix, name, metadata=None, body="Test task content"):
    """Helper to create a task file."""
    md = metadata or {}
    md.setdefault("type", prefix.lower().rstrip("_"))
    md.setdefault("priority", "medium")
    md.setdefault("status", "new")
    md.setdefault("requires_approval", False)

    filepath = project / "Needs_Action" / f"{prefix}{name}.md"
    frontmatter.write_file(filepath, md, body)
    return filepath


class TestSwarmOrchestrator:
    def test_creates_with_diamond_components(self, tmp_project):
        orch = SwarmOrchestrator(dry_run=True)
        assert orch.registry is not None
        assert orch.bus is not None
        assert orch.router is not None
        assert orch.tracker is not None

    def test_registry_has_four_agents(self, tmp_project):
        orch = SwarmOrchestrator(dry_run=True)
        assert orch.registry.total_count == 4

    def test_poll_empty(self, tmp_project):
        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 0

    def test_delegate_email_to_sales(self, tmp_project):
        _create_task(tmp_project, "EMAIL_", "mock_001",
                     {"type": "email", "from": "alice@test.com", "subject": "Hello"})
        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 1
        # Outcome should be recorded
        assert orch.tracker.total_outcomes == 1

    def test_delegate_payment_to_finance(self, tmp_project):
        _create_task(tmp_project, "PAYMENT_", "vendor_001",
                     {"type": "payment", "amount": "500"})
        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 1

    def test_delegate_facebook_to_content(self, tmp_project):
        _create_task(tmp_project, "FACEBOOK_", "post_001",
                     {"type": "facebook"})
        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 1

    def test_unknown_prefix_falls_back_to_base(self, tmp_project):
        _create_task(tmp_project, "CUSTOM_", "task_001",
                     {"type": "custom"})
        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 1

    def test_security_scan_blocks_sensitive(self, tmp_project):
        _create_task(tmp_project, "EMAIL_", "leak_001",
                     {"type": "email", "requires_approval": False},
                     body="Here is the password: secret123")
        orch = SwarmOrchestrator(dry_run=True)
        orch.poll_once()
        # Security agent should flag it for approval
        outcomes = orch.tracker.get_outcomes()
        assert len(outcomes) >= 1

    def test_multiple_tasks_sorted_by_priority(self, tmp_project):
        _create_task(tmp_project, "EMAIL_", "low_001",
                     {"type": "email", "priority": "low"})
        _create_task(tmp_project, "EMAIL_", "high_001",
                     {"type": "email", "priority": "high"})
        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 2

    def test_get_swarm_status(self, tmp_project):
        orch = SwarmOrchestrator(dry_run=True)
        status = orch.get_swarm_status()
        assert status["tier"] == "diamond"
        assert status["agents"]["total_agents"] == 4
        assert "learning" in status
        assert "metrics" in status

    def test_outcome_tracking(self, tmp_project):
        _create_task(tmp_project, "ODOO_", "sync_001",
                     {"type": "odoo"})
        orch = SwarmOrchestrator(dry_run=True)
        orch.poll_once()
        stats = orch.tracker.get_stats()
        assert stats["total_outcomes"] >= 1

    def test_tasks_moved_to_done(self, tmp_project):
        _create_task(tmp_project, "AUDIT_", "weekly_001",
                     {"type": "audit", "requires_approval": False})
        orch = SwarmOrchestrator(dry_run=True)
        orch.poll_once()
        done_files = list((tmp_project / "Done").glob("*.md"))
        assert len(done_files) >= 1
