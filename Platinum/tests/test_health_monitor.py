"""Tests for src.health — heartbeat and health monitor."""

import json
import time
import pytest
from pathlib import Path

from src.health.heartbeat import write_heartbeat, read_heartbeat, heartbeat_age
from src.health.health_monitor import HealthMonitor


@pytest.fixture
def tmp_project(tmp_path, monkeypatch):
    """Set up a temporary project with required folders."""
    monkeypatch.setattr("src.utils.file_ops.get_project_root", lambda: tmp_path)
    monkeypatch.setattr("src.health.heartbeat.get_project_root", lambda: tmp_path)

    (tmp_path / "Logs").mkdir()
    (tmp_path / "Needs_Action").mkdir()
    return tmp_path


class TestHeartbeat:
    def test_write_heartbeat(self, tmp_project):
        path = write_heartbeat("test-agent")
        assert path.exists()
        assert ".heartbeat_test-agent.json" in path.name

    def test_read_heartbeat(self, tmp_project):
        write_heartbeat("test-agent")
        hb = read_heartbeat("test-agent")
        assert hb is not None
        assert hb["agent_id"] == "test-agent"
        assert hb["status"] == "alive"

    def test_read_heartbeat_missing(self, tmp_project):
        hb = read_heartbeat("nonexistent-agent")
        assert hb is None

    def test_heartbeat_age(self, tmp_project):
        write_heartbeat("test-agent")
        age = heartbeat_age("test-agent")
        assert age is not None
        assert age < 5  # Should be very recent

    def test_heartbeat_age_missing(self, tmp_project):
        age = heartbeat_age("nonexistent")
        assert age is None


class TestHealthMonitor:
    def test_check_heartbeat_fresh(self, tmp_project):
        write_heartbeat("test-agent")
        monitor = HealthMonitor(stale_threshold=120)
        result = monitor.check_heartbeat("test-agent")
        assert result["healthy"] is True
        assert result["status"] == "healthy"

    def test_check_heartbeat_missing(self, tmp_project):
        monitor = HealthMonitor()
        result = monitor.check_heartbeat("missing-agent")
        assert result["healthy"] is False
        assert result["status"] == "no_heartbeat"

    def test_check_disk_usage_mock(self, tmp_project):
        monitor = HealthMonitor()
        result = monitor.check_disk_usage()
        assert result["healthy"] is True
        assert result["mock"] is True

    def test_check_error_rate_no_data(self, tmp_project):
        monitor = HealthMonitor()
        result = monitor.check_error_rate()
        assert result["healthy"] is True
        assert result["error_count"] == 0

    def test_run_all_checks(self, tmp_project):
        write_heartbeat("cloud-001")
        write_heartbeat("local-001")

        monitor = HealthMonitor()
        report = monitor.run_all_checks(["cloud-001", "local-001"])
        assert report["overall_status"] == "healthy"
        assert "heartbeats" in report
        assert "disk" in report
        assert "error_rate" in report

    def test_run_all_checks_degraded(self, tmp_project):
        # Only write one heartbeat — the other will be missing
        write_heartbeat("cloud-001")

        monitor = HealthMonitor()
        report = monitor.run_all_checks(["cloud-001", "missing-agent"])
        assert report["overall_status"] == "degraded"

    def test_writes_health_report(self, tmp_project):
        write_heartbeat("cloud-001")
        monitor = HealthMonitor()
        monitor.run_all_checks(["cloud-001"])

        health_files = list((tmp_project / "Logs").glob("*_health.md"))
        assert len(health_files) == 1

    def test_creates_alert_on_failure(self, tmp_project):
        monitor = HealthMonitor()
        monitor.run_all_checks(["missing-agent"])

        alert_files = list((tmp_project / "Needs_Action").glob("ERROR_*.md"))
        assert len(alert_files) == 1
