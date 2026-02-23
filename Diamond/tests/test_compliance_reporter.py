"""Tests for compliance reporter."""

import json
import pytest
from pathlib import Path
from src.compliance.compliance_reporter import ComplianceReporter
from src.learning.outcome_tracker import OutcomeTracker, TaskOutcome, Outcome


@pytest.fixture
def project(tmp_path):
    """Create a mock project structure."""
    for folder in ["Done", "Errors", "Logs", "Pending_Approval", "Approved", "Briefings"]:
        (tmp_path / folder).mkdir()
    return tmp_path


class TestComplianceReporter:
    def test_clean_compliance_check(self, project):
        import time
        # Create a fresh audit log so the check doesn't flag missing log
        log_path = project / "Logs" / "audit.jsonl"
        log_path.write_text(json.dumps({"timestamp": time.time(), "action": "init"}) + "\n")

        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        assert report["status"] == "compliant"
        assert len(report["violations"]) == 0

    def test_error_accumulation_violation(self, project):
        errors_dir = project / "Errors"
        for i in range(15):
            (errors_dir / f"ERROR_{i:03d}.md").write_text("error")

        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        assert report["status"] == "non_compliant"
        assert any(v["type"] == "error_accumulation" for v in report["violations"])

    def test_missing_audit_log(self, project):
        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        checks = {c["name"]: c for c in report["checks"]}
        assert checks["audit_log"]["status"] == "warn"

    def test_fresh_audit_log(self, project):
        import time
        log_path = project / "Logs" / "audit.jsonl"
        entry = json.dumps({"timestamp": time.time(), "action": "test"})
        log_path.write_text(entry + "\n")

        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        checks = {c["name"]: c for c in report["checks"]}
        assert checks["audit_log"]["status"] == "pass"

    def test_low_success_rate_check(self, project):
        tracker = OutcomeTracker()
        for _ in range(10):
            tracker.record(TaskOutcome(
                task_id="t", task_type="email", agent_id="a",
                agent_type="sales", outcome=Outcome.FAILURE,
                duration_ms=100,
            ))

        reporter = ComplianceReporter(project, tracker=tracker)
        report = reporter.run_compliance_check()
        checks = {c["name"]: c for c in report["checks"]}
        assert checks["completion_rates"]["status"] == "fail"

    def test_generate_report_md(self, project):
        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        md = reporter.generate_report_md(report)
        assert "# Compliance Report" in md
        assert "Checks" in md

    def test_save_report(self, project):
        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        path = reporter.save_report(report)
        assert path.exists()
        assert "compliance_" in path.name

    def test_approval_pipeline_check(self, project):
        reporter = ComplianceReporter(project)
        report = reporter.run_compliance_check()
        checks = {c["name"]: c for c in report["checks"]}
        assert "approval_pipeline" in checks
