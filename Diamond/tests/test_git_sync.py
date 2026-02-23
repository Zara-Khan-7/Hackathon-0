"""Tests for src.sync — GitVaultSync, conflict_resolver, SyncWatcher."""

import time
import pytest

from src.sync.git_sync import GitVaultSync
from src.sync.conflict_resolver import resolve_conflicts, get_strategy
from src.sync.sync_watcher import SyncWatcher


class TestGitVaultSync:
    def test_pull_returns_success(self):
        sync = GitVaultSync("test-agent")
        result = sync.pull()
        assert result["status"] == "success"
        assert result["mock"] is True
        assert result["operation"] == "pull"

    def test_push_returns_success(self):
        sync = GitVaultSync("test-agent")
        result = sync.push()
        assert result["status"] == "success"
        assert result["operation"] == "push"

    def test_push_custom_message(self):
        sync = GitVaultSync("test-agent")
        result = sync.push(message="Custom commit message")
        assert result["message"] == "Custom commit message"

    def test_sync_cycle(self):
        sync = GitVaultSync("test-agent")
        result = sync.sync_cycle()
        assert result["status"] == "success"
        assert "pull" in result
        assert "push" in result

    def test_pull_count_increments(self):
        sync = GitVaultSync("test-agent")
        sync.pull()
        sync.pull()
        sync.pull()
        status = sync.get_status()
        assert status["pull_count"] == 3

    def test_push_count_increments(self):
        sync = GitVaultSync("test-agent")
        sync.push()
        sync.push()
        status = sync.get_status()
        assert status["push_count"] == 2

    def test_get_status(self):
        sync = GitVaultSync("test-agent", remote="origin", branch="main")
        status = sync.get_status()
        assert status["agent_id"] == "test-agent"
        assert status["remote"] == "origin/main"


class TestConflictResolver:
    def test_needs_action_keeps_theirs(self):
        result = resolve_conflicts("Needs_Action", "local content", "remote content")
        assert result == "remote content"

    def test_in_progress_keeps_ours(self):
        result = resolve_conflicts("In_Progress", "local content", "remote content")
        assert result == "local content"

    def test_logs_union_merge(self):
        result = resolve_conflicts("Logs", "line A\nline B\n", "line B\nline C\n")
        assert "line B" in result
        assert "line C" in result

    def test_strategy_defaults(self):
        assert get_strategy("Needs_Action") == "theirs"
        assert get_strategy("In_Progress") == "ours"
        assert get_strategy("Logs") == "union"
        assert get_strategy("Done") == "union"
        assert get_strategy("Unknown") == "theirs"


class TestSyncWatcher:
    def test_pull_once(self):
        watcher = SyncWatcher("test-agent", interval=60)
        result = watcher.pull_once()
        assert result["status"] == "success"

    def test_start_stop(self):
        watcher = SyncWatcher("test-agent", interval=1)
        watcher.start()
        assert watcher.is_running is True
        time.sleep(0.1)
        watcher.stop()
        assert watcher.is_running is False

    def test_not_running_by_default(self):
        watcher = SyncWatcher("test-agent")
        assert watcher.is_running is False
