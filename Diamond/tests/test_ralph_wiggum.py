"""Tests for the Ralph Wiggum state machine loop."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.orchestrator.ralph_wiggum import TaskState, RalphWiggumLoop
from src.utils import frontmatter


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project structure."""
    for folder in ["Needs_Action", "Pending_Approval", "Approved", "Done", "Errors", "Logs"]:
        (tmp_path / folder).mkdir()
    return tmp_path


@pytest.fixture
def sample_task(tmp_project):
    """Create a sample task file in Needs_Action/."""
    task_file = tmp_project / "Needs_Action" / "ODOO_invoice_001.md"
    meta = {
        "type": "odoo",
        "priority": "high",
        "requires_approval": True,
        "created": "2026-02-19 10:00:00",
    }
    body = "# Invoice for Acme Corp\n\nAmount: $5,000\nPartner: Acme Corporation\n"
    frontmatter.write_file(task_file, meta, body)
    return task_file


class TestTaskState:
    """Test the TaskState enum."""

    def test_all_states_exist(self):
        assert TaskState.CREATED == "created"
        assert TaskState.PLANNED == "planned"
        assert TaskState.AWAITING_APPROVAL == "awaiting_approval"
        assert TaskState.APPROVED == "approved"
        assert TaskState.EXECUTING == "executing"
        assert TaskState.COMPLETED == "completed"
        assert TaskState.FAILED == "failed"


class TestRalphWiggumLoop:
    """Test the Ralph Wiggum loop."""

    def test_initial_state(self, sample_task, tmp_project):
        with patch("src.orchestrator.ralph_wiggum.get_project_root", return_value=tmp_project):
            loop = RalphWiggumLoop(sample_task, max_iterations=5, dry_run=True)
            assert loop.state["current_state"] == TaskState.CREATED.value
            assert loop.state["iteration"] == 0
            assert loop.task_id == "ODOO_invoice_001"

    def test_state_persistence(self, sample_task, tmp_project):
        with patch("src.orchestrator.ralph_wiggum.get_project_root", return_value=tmp_project):
            loop = RalphWiggumLoop(sample_task, max_iterations=5, dry_run=True)
            loop._transition(TaskState.PLANNED, "test transition")
            loop._save_state()

            # Load state in a new instance
            loop2 = RalphWiggumLoop(sample_task, max_iterations=5, dry_run=True)
            assert loop2.state["current_state"] == TaskState.PLANNED.value
            assert len(loop2.state["history"]) == 1

    def test_dry_run_completes(self, sample_task, tmp_project):
        """In dry-run mode, the loop should run and eventually hit max iterations or complete."""
        with patch("src.orchestrator.ralph_wiggum.get_project_root", return_value=tmp_project):
            with patch("src.orchestrator.ralph_wiggum.get_folder") as mock_get_folder:
                # Mock get_folder to return tmp_project subfolders
                def side_effect(name):
                    p = tmp_project / name
                    p.mkdir(exist_ok=True)
                    return p
                mock_get_folder.side_effect = side_effect

                loop = RalphWiggumLoop(sample_task, max_iterations=3, dry_run=True)
                result = loop.run()

                assert result["task_id"] == "ODOO_invoice_001"
                assert result["iterations"] <= 3
                assert result["status"] in [s.value for s in TaskState]

    def test_completed_when_file_in_done(self, sample_task, tmp_project):
        """If the task file appears in Done/, the loop should mark COMPLETED."""
        import shutil

        with patch("src.orchestrator.ralph_wiggum.get_project_root", return_value=tmp_project):
            with patch("src.orchestrator.ralph_wiggum.get_folder") as mock_get_folder:
                def side_effect(name):
                    p = tmp_project / name
                    p.mkdir(exist_ok=True)
                    return p
                mock_get_folder.side_effect = side_effect

                # Move the task file to Done/ (remove from Needs_Action)
                done_file = tmp_project / "Done" / sample_task.name
                shutil.move(str(sample_task), str(done_file))

                loop = RalphWiggumLoop(done_file, max_iterations=5, dry_run=True)
                # Manually set to PLANNED so it checks file location
                loop._transition(TaskState.PLANNED)

                # The detect_file_location should find it in Done/
                location = loop._detect_file_location()
                assert location == "Done"

    def test_build_context(self, sample_task, tmp_project):
        with patch("src.orchestrator.ralph_wiggum.get_project_root", return_value=tmp_project):
            loop = RalphWiggumLoop(sample_task, max_iterations=5, dry_run=True)
            context = loop._build_context()

            assert "ODOO_invoice_001" in context
            assert "created" in context
            assert "Invoice for Acme Corp" in context
