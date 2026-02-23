"""Tests for src.claim.claim_manager — claim-by-move task ownership."""

import time
import pytest
from pathlib import Path
from unittest.mock import patch

from src.claim.claim_manager import ClaimManager
from src.utils.file_ops import get_folder


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Set up a temporary project with Needs_Action and In_Progress folders."""
    monkeypatch.setattr("src.utils.file_ops.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("src.claim.claim_manager.get_project_root", lambda: tmp_path)

    (tmp_path / "Needs_Action").mkdir()
    (tmp_path / "In_Progress").mkdir()
    return tmp_path


@pytest.fixture
def sample_task(tmp_project):
    """Create a sample task in Needs_Action/."""
    task = tmp_project / "Needs_Action" / "EMAIL_mock_001.md"
    task.write_text("---\ntype: email\n---\nTest task\n")
    return task


class TestClaimManager:
    def test_claim_moves_file(self, tmp_project, sample_task):
        cm = ClaimManager("test-agent")
        result = cm.claim(sample_task)

        assert result is not None
        assert result.exists()
        assert not sample_task.exists()
        assert "test-agent" in str(result)

    def test_claim_nonexistent_returns_none(self, tmp_project):
        cm = ClaimManager("test-agent")
        result = cm.claim(tmp_project / "nonexistent.md")
        assert result is None

    def test_claim_already_claimed_returns_none(self, tmp_project, sample_task):
        cm = ClaimManager("test-agent")
        cm.claim(sample_task)

        # Create another file with same name
        dup = tmp_project / "Needs_Action" / "EMAIL_mock_001.md"
        dup.write_text("dup\n")
        result = cm.claim(dup)
        assert result is None

    def test_unclaim_moves_back(self, tmp_project, sample_task):
        cm = ClaimManager("test-agent")
        claimed = cm.claim(sample_task)
        assert claimed is not None

        result = cm.unclaim(claimed)
        assert result is not None
        assert result.exists()
        assert "Needs_Action" in str(result)

    def test_list_claimed(self, tmp_project, sample_task):
        cm = ClaimManager("test-agent")
        cm.claim(sample_task)

        claimed = cm.list_claimed()
        assert len(claimed) == 1
        assert claimed[0].name == "EMAIL_mock_001.md"

    def test_is_claimed(self, tmp_project, sample_task):
        cm = ClaimManager("test-agent")
        assert cm.is_claimed("EMAIL_mock_001.md") is False

        cm.claim(sample_task)
        assert cm.is_claimed("EMAIL_mock_001.md") is True

    def test_get_claim_owner(self, tmp_project, sample_task):
        cm = ClaimManager("test-agent")
        assert cm.get_claim_owner("EMAIL_mock_001.md") is None

        cm.claim(sample_task)
        assert cm.get_claim_owner("EMAIL_mock_001.md") == "test-agent"

    def test_cleanup_stale(self, tmp_project):
        cm = ClaimManager("old-agent")
        agent_folder = tmp_project / "In_Progress" / "old-agent"
        agent_folder.mkdir(parents=True)

        stale = agent_folder / "STALE_task.md"
        stale.write_text("stale task\n")
        # Set mtime to 2 hours ago
        old_time = time.time() - 7200
        import os
        os.utime(str(stale), (old_time, old_time))

        cleanup_cm = ClaimManager("cleanup-agent")
        moved = cleanup_cm.cleanup_stale(max_age_seconds=3600)

        assert len(moved) == 1
        assert (tmp_project / "Needs_Action" / "STALE_task.md").exists()

    def test_cleanup_fresh_not_moved(self, tmp_project):
        cm = ClaimManager("active-agent")
        agent_folder = tmp_project / "In_Progress" / "active-agent"
        agent_folder.mkdir(parents=True)

        fresh = agent_folder / "FRESH_task.md"
        fresh.write_text("fresh task\n")

        moved = cm.cleanup_stale(max_age_seconds=3600)
        assert len(moved) == 0
        assert fresh.exists()
