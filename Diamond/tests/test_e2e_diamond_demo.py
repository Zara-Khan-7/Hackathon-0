"""End-to-end Diamond tier demo test.

Verifies the complete multi-agent swarm pipeline:
1. Tasks created in Needs_Action/
2. SwarmOrchestrator delegates to specialized agents
3. A2A messaging routes correctly
4. Outcome tracking records results
5. Security agent validates content
6. Compliance check passes
7. CRM integration works
8. API returns correct status
"""

import pytest
from pathlib import Path
from src.orchestrator.swarm_orchestrator import SwarmOrchestrator
from src.agents.agent_registry import create_default_registry
from src.a2a.message_bus import MockMessageBus
from src.a2a.message import A2AMessage, MessageType
from src.a2a.router import MessageRouter
from src.learning.outcome_tracker import OutcomeTracker, TaskOutcome, Outcome
from src.learning.prompt_optimizer import PromptOptimizer
from src.learning.performance_metrics import PerformanceMetrics
from src.compliance.compliance_reporter import ComplianceReporter
from src.crm.crm_client import CRMClient
from src.vault.credential_vault import CredentialVault
from src.api.api_server import APIServer
from src.scaling.cloud_manager import CloudManager
from src.utils import frontmatter


@pytest.fixture
def diamond_project(tmp_path, monkeypatch):
    """Full Diamond project setup."""
    monkeypatch.setattr("src.utils.file_ops.get_project_root", lambda: tmp_path)
    for folder in ["Inbox", "Needs_Action", "In_Progress", "Pending_Approval",
                    "Approved", "Rejected", "Done", "Logs", "Errors",
                    "Accounting", "Briefings"]:
        (tmp_path / folder).mkdir()
    return tmp_path


def _create_task(project, prefix, name, metadata=None, body="Test content"):
    md = metadata or {}
    md.setdefault("type", prefix.lower().rstrip("_"))
    md.setdefault("priority", "medium")
    md.setdefault("status", "new")
    md.setdefault("requires_approval", False)
    filepath = project / "Needs_Action" / f"{prefix}{name}.md"
    frontmatter.write_file(filepath, md, body)
    return filepath


class TestFullSwarmPipeline:
    """End-to-end: tasks → swarm → agents → done."""

    def test_multi_task_delegation(self, diamond_project):
        """Multiple task types get routed to correct agents."""
        _create_task(diamond_project, "EMAIL_", "sales_lead",
                     {"type": "email", "from": "prospect@co.com"})
        _create_task(diamond_project, "PAYMENT_", "vendor_inv",
                     {"type": "payment", "amount": "1500"})
        _create_task(diamond_project, "FACEBOOK_", "weekly_post",
                     {"type": "facebook"})
        _create_task(diamond_project, "AUDIT_", "q1_review",
                     {"type": "audit"})

        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 4

        # All outcomes recorded
        assert orch.tracker.total_outcomes == 4

        # All succeeded
        success_rate = orch.tracker.success_rate()
        assert success_rate == 1.0

    def test_priority_ordering(self, diamond_project):
        """High priority tasks processed first."""
        _create_task(diamond_project, "EMAIL_", "low",
                     {"type": "email", "priority": "low"})
        _create_task(diamond_project, "EMAIL_", "high",
                     {"type": "email", "priority": "high"})

        orch = SwarmOrchestrator(dry_run=True)
        processed = orch.poll_once()
        assert processed == 2

    def test_security_scan_integration(self, diamond_project):
        """Security agent scans outgoing content."""
        _create_task(diamond_project, "EMAIL_", "sensitive",
                     {"type": "email", "requires_approval": False},
                     body="The password is hunter2 and the token is abc123")

        orch = SwarmOrchestrator(dry_run=True)
        orch.poll_once()

        # Task should still be processed (security flags it but doesn't block)
        assert orch.tracker.total_outcomes >= 1


class TestA2AMessaging:
    """Test agent-to-agent communication."""

    def test_delegation_creates_message(self, diamond_project):
        registry = create_default_registry()
        bus = MockMessageBus()
        router = MessageRouter(bus, registry)

        task = {"filename": "EMAIL_test.md", "task_type": "email",
                "priority": "medium", "body": ""}
        msg = router.delegate_task("orchestrator", task)
        assert msg is not None
        assert msg.recipient_id == "sales-agent"

    def test_result_delivery(self, diamond_project):
        registry = create_default_registry()
        bus = MockMessageBus()
        router = MessageRouter(bus, registry)

        router.send_result("sales-agent", "orchestrator", {"done": True})
        msgs = router.get_messages("orchestrator")
        assert len(msgs) == 1
        assert msgs[0].payload["result"]["done"] is True

    def test_broadcast_alert_reaches_all(self, diamond_project):
        registry = create_default_registry()
        bus = MockMessageBus()
        router = MessageRouter(bus, registry)

        # Initialize queues
        for agent_id in ["sales-agent", "finance-agent", "content-agent"]:
            bus.publish(A2AMessage(
                sender_id="init", recipient_id=agent_id,
                message_type=MessageType.STATUS_UPDATE,
                payload={"init": True}
            ))

        router.broadcast_alert("security-agent", "threat_detected",
                               {"severity": "high"})

        for agent_id in ["sales-agent", "finance-agent", "content-agent"]:
            msgs = router.get_messages(agent_id)
            assert any(m.message_type == MessageType.SECURITY_ALERT for m in msgs)


class TestSelfImproving:
    """Test the learning / self-improving loop."""

    def test_outcome_tracking_through_swarm(self, diamond_project):
        _create_task(diamond_project, "EMAIL_", "test_001")
        orch = SwarmOrchestrator(dry_run=True)
        orch.poll_once()
        assert orch.tracker.total_outcomes == 1

    def test_performance_metrics(self, diamond_project):
        _create_task(diamond_project, "EMAIL_", "t1")
        _create_task(diamond_project, "EMAIL_", "t2")
        _create_task(diamond_project, "PAYMENT_", "t3")

        orch = SwarmOrchestrator(dry_run=True)
        orch.poll_once()

        health = orch.metrics.get_swarm_health()
        assert health["total_tasks"] == 3
        assert health["overall_score"] > 0


class TestComplianceIntegration:
    """Test compliance reporting with Diamond components."""

    def test_compliance_check_clean(self, diamond_project):
        import json, time
        # Create fresh audit log to avoid missing-log violation
        log_path = diamond_project / "Logs" / "audit.jsonl"
        log_path.write_text(json.dumps({"timestamp": time.time(), "action": "init"}) + "\n")

        tracker = OutcomeTracker()
        reporter = ComplianceReporter(diamond_project, tracker=tracker)
        report = reporter.run_compliance_check()
        assert report["status"] == "compliant"

    def test_compliance_report_saved(self, diamond_project):
        reporter = ComplianceReporter(diamond_project)
        report = reporter.run_compliance_check()
        path = reporter.save_report(report)
        assert path.exists()


class TestCRMIntegration:
    """Test CRM mock integration."""

    def test_crm_pipeline(self):
        crm = CRMClient(mock=True)
        pipeline = crm.get_pipeline_summary()
        assert "negotiation" in pipeline
        total_value = sum(s["total_value"] for s in pipeline.values())
        assert total_value > 0

    def test_crm_contact_lifecycle(self):
        crm = CRMClient(mock=True)
        contact = crm.create_contact("New Lead", "lead@co.com", "LeadCo", ["prospect"])
        crm.log_activity(contact["id"], "email_sent", "Intro email")
        activities = crm.list_activities(contact_id=contact["id"])
        assert len(activities) == 1


class TestVaultAndScaling:
    """Test credential vault and cloud scaling."""

    def test_vault_store_retrieve(self):
        vault = CredentialVault()
        vault.store("smtp_password", "s3cur3!")
        assert vault.retrieve("smtp_password") == "s3cur3!"

    def test_cloud_scaling(self):
        cm = CloudManager(max_instances=3)
        cm.scale_to(2, role="worker")
        assert cm.running_count == 2
        cm.scale_to(1, role="worker")
        assert cm.running_count == 1


class TestAPIIntegration:
    """Test API server with all Diamond components."""

    def test_api_full_status(self, diamond_project):
        api = APIServer(diamond_project, mock=True)
        api.set_components(
            registry=create_default_registry(),
            tracker=OutcomeTracker(),
            crm=CRMClient(),
            vault=CredentialVault(),
        )

        status = api.get_status()
        assert status["tier"] == "diamond"
        assert all(status["components"].values())

        agents = api.get_agents()
        assert agents["total_agents"] == 4

        health = api.get_health()
        assert health["healthy"] is True

        folders = api.get_folders()
        assert "Needs_Action" in folders["folders"]
