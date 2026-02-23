"""Tests for the weekly business auditor."""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.audit.auditor import WeeklyAuditor
from src.utils import frontmatter


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project structure with sample data."""
    for folder in ["Needs_Action", "Pending_Approval", "Approved", "Rejected",
                    "Done", "Logs", "Errors", "Accounting", "Briefings"]:
        (tmp_path / folder).mkdir()

    # Create some Done/ tasks
    for i, prefix in enumerate(["EMAIL", "LINKEDIN", "ODOO", "FACEBOOK"]):
        task_file = tmp_path / "Done" / f"{prefix}_task_{i}.md"
        meta = {"type": prefix.lower(), "priority": "medium", "created": "2026-02-19 10:00:00"}
        frontmatter.write_file(task_file, meta, f"# Completed {prefix} task\n")

    # Create a pending task
    pending = tmp_path / "Needs_Action" / "EMAIL_old.md"
    meta = {"type": "email", "priority": "medium", "created": "2026-02-10 10:00:00"}
    frontmatter.write_file(pending, meta, "# Old task\n")

    # Create an error
    error = tmp_path / "Errors" / "ERROR_fail.md"
    meta = {"type": "error", "status": "failed", "max_retries": 3, "created": "2026-02-18 10:00:00"}
    frontmatter.write_file(error, meta, "# Failed task\n")

    return tmp_path


class TestWeeklyAuditor:
    """Test the WeeklyAuditor in mock mode."""

    def test_gather_task_stats(self, tmp_project):
        with patch("src.utils.file_ops.get_project_root", return_value=tmp_project):
            auditor = WeeklyAuditor(mock=True)
            stats = auditor.gather_task_stats()

            assert stats["total_done"] == 4
            assert stats["pending_tasks"] == 1
            assert "EMAIL" in stats["done_by_type"]

    def test_gather_odoo_stats_mock(self, tmp_project):
        with patch("src.utils.file_ops.get_project_root", return_value=tmp_project):
            auditor = WeeklyAuditor(mock=True)
            stats = auditor.gather_odoo_stats()

            assert "total_revenue_collected" in stats
            assert "outstanding_amount" in stats
            assert "draft_invoices" in stats
            assert stats["total_invoices"] >= 0

    def test_gather_social_stats_mock(self, tmp_project):
        with patch("src.utils.file_ops.get_project_root", return_value=tmp_project):
            auditor = WeeklyAuditor(mock=True)
            stats = auditor.gather_social_stats()

            assert isinstance(stats, dict)
            assert "facebook" in stats
            assert "instagram" in stats
            assert "twitter" in stats

    def test_detect_bottlenecks(self, tmp_project):
        with patch("src.utils.file_ops.get_project_root", return_value=tmp_project):
            auditor = WeeklyAuditor(mock=True)
            bottlenecks = auditor.detect_bottlenecks()

            # Should detect the old pending task and the failed error
            assert len(bottlenecks) >= 1
            issues = [b["issue"] for b in bottlenecks]
            assert any("Stuck" in i or "Failed" in i for i in issues)

    def test_generate_briefing(self, tmp_project):
        with patch("src.utils.file_ops.get_project_root", return_value=tmp_project):
            with patch("src.utils.file_ops.get_folder") as mock_get_folder:
                def side_effect(name):
                    p = tmp_project / name
                    p.mkdir(exist_ok=True)
                    return p
                mock_get_folder.side_effect = side_effect

                auditor = WeeklyAuditor(mock=True)
                path = auditor.generate_briefing()

                assert path.exists()
                assert "Monday_Briefing" in path.name

                content = path.read_text(encoding="utf-8")
                assert "Executive Summary" in content
                assert "Revenue" in content
                assert "Social Media" in content
                assert "Bottlenecks" in content
