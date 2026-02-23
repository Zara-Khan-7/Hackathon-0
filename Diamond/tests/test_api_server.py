"""Tests for REST API server (mock mode)."""

import pytest
from pathlib import Path
from src.api.api_server import APIServer
from src.agents.agent_registry import create_default_registry
from src.learning.outcome_tracker import OutcomeTracker
from src.crm.crm_client import CRMClient
from src.vault.credential_vault import CredentialVault


@pytest.fixture
def api(tmp_path):
    for folder in ["Needs_Action", "Done", "Logs", "Errors", "In_Progress",
                    "Pending_Approval", "Approved", "Rejected", "Inbox",
                    "Accounting", "Briefings"]:
        (tmp_path / folder).mkdir()
    server = APIServer(tmp_path, mock=True)
    server.set_components(
        registry=create_default_registry(),
        tracker=OutcomeTracker(),
        crm=CRMClient(mock=True),
        vault=CredentialVault(),
    )
    return server


class TestAPIServer:
    def test_get_status(self, api):
        status = api.get_status()
        assert status["status"] == "running"
        assert status["tier"] == "diamond"
        assert status["mock_mode"] is True

    def test_get_agents(self, api):
        agents = api.get_agents()
        assert agents["total_agents"] == 4
        assert len(agents["agents"]) == 4

    def test_get_tasks_empty(self, api):
        tasks = api.get_tasks("Needs_Action")
        assert tasks["count"] == 0

    def test_get_tasks_with_files(self, api, tmp_path):
        (tmp_path / "Needs_Action" / "EMAIL_001.md").write_text("test")
        tasks = api.get_tasks("Needs_Action")
        assert tasks["count"] == 1

    def test_get_metrics(self, api):
        metrics = api.get_metrics()
        assert "total_outcomes" in metrics

    def test_get_crm_summary(self, api):
        crm = api.get_crm_summary()
        assert crm["total_contacts"] == 3

    def test_get_health(self, api):
        health = api.get_health()
        assert health["healthy"] is True
        assert health["checks"]["api"] == "ok"

    def test_get_folders(self, api):
        folders = api.get_folders()
        assert "Needs_Action" in folders["folders"]
        assert "Done" in folders["folders"]

    def test_no_components(self, tmp_path):
        server = APIServer(tmp_path, mock=True)
        agents = server.get_agents()
        assert "error" in agents
        metrics = server.get_metrics()
        assert "error" in metrics

    def test_stats(self, api):
        stats = api.get_stats()
        assert stats["mock_mode"] is True
        assert stats["endpoints"] == 7

    def test_run_mock_mode(self, api):
        result = api.run()
        assert result["mock"] is True
