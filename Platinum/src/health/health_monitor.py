"""Health monitor — checks heartbeats, disk, error rate, generates alerts.

Writes health reports to Logs/ and creates ERROR_HEALTH_*.md on critical issues.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from src.health.heartbeat import heartbeat_age, read_heartbeat
from src.utils.file_ops import get_project_root, get_folder, create_task_file
from src.utils.logger import log_action, log_error


class HealthMonitor:
    """Monitors system health and generates alerts."""

    def __init__(self, stale_threshold: int = 120, disk_warn_percent: int = 90,
                 error_rate_threshold: int = 5):
        self.stale_threshold = stale_threshold
        self.disk_warn_percent = disk_warn_percent
        self.error_rate_threshold = error_rate_threshold
        self.project_root = get_project_root()

    def check_heartbeat(self, agent_id: str) -> dict:
        """Check if an agent's heartbeat is fresh."""
        age = heartbeat_age(agent_id)
        if age is None:
            return {"agent_id": agent_id, "status": "no_heartbeat", "healthy": False}

        healthy = age < self.stale_threshold
        return {
            "agent_id": agent_id,
            "status": "healthy" if healthy else "stale",
            "age_seconds": round(age, 1),
            "threshold": self.stale_threshold,
            "healthy": healthy,
        }

    def check_disk_usage(self) -> dict:
        """Check disk usage (mock — always returns safe values)."""
        return {
            "status": "healthy",
            "used_percent": 45,
            "warn_threshold": self.disk_warn_percent,
            "healthy": True,
            "mock": True,
        }

    def check_error_rate(self) -> dict:
        """Check recent error rate from audit logs."""
        audit_file = get_folder("Logs") / f"{datetime.now().strftime('%Y-%m-%d')}_actions.jsonl"
        if not audit_file.exists():
            return {"status": "no_data", "error_count": 0, "healthy": True}

        error_count = 0
        one_hour_ago = time.time() - 3600

        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("result") == "failed":
                            error_count += 1
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass

        healthy = error_count < self.error_rate_threshold
        return {
            "status": "healthy" if healthy else "high_error_rate",
            "error_count": error_count,
            "threshold": self.error_rate_threshold,
            "healthy": healthy,
        }

    def run_all_checks(self, agent_ids: list[str] | None = None) -> dict:
        """Run all health checks and return combined report."""
        if agent_ids is None:
            agent_ids = ["cloud-001", "local-001"]

        heartbeats = {aid: self.check_heartbeat(aid) for aid in agent_ids}
        disk = self.check_disk_usage()
        errors = self.check_error_rate()

        all_healthy = (
            all(h["healthy"] for h in heartbeats.values())
            and disk["healthy"]
            and errors["healthy"]
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if all_healthy else "degraded",
            "heartbeats": heartbeats,
            "disk": disk,
            "error_rate": errors,
        }

        # Write health report
        self._write_report(report)

        # Create alert if unhealthy
        if not all_healthy:
            self._create_alert(report)

        return report

    def _write_report(self, report: dict) -> Path:
        """Write health report to Logs/."""
        logs_dir = get_folder("Logs")
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_path = logs_dir / f"{date_str}_health.md"

        content = f"# Health Report\n\n"
        content += f"**Time:** {report['timestamp']}\n"
        content += f"**Status:** {report['overall_status']}\n\n"

        content += "## Heartbeats\n\n"
        for agent_id, check in report["heartbeats"].items():
            status = check["status"]
            content += f"- **{agent_id}:** {status}\n"

        content += f"\n## Disk Usage\n\n"
        content += f"- Used: {report['disk']['used_percent']}%\n"

        content += f"\n## Error Rate\n\n"
        content += f"- Errors: {report['error_rate']['error_count']}\n"

        report_path.write_text(content, encoding="utf-8")
        log_action("Health report written", report_path.name, "health")
        return report_path

    def _create_alert(self, report: dict) -> Path:
        """Create an ERROR_HEALTH_ task for critical health issues."""
        issues = []

        for agent_id, check in report["heartbeats"].items():
            if not check["healthy"]:
                issues.append(f"Agent {agent_id}: {check['status']}")

        if not report["disk"]["healthy"]:
            issues.append(f"Disk usage: {report['disk']['used_percent']}%")

        if not report["error_rate"]["healthy"]:
            issues.append(f"High error rate: {report['error_rate']['error_count']} errors")

        metadata = {
            "type": "health_alert",
            "priority": "high",
            "status": report["overall_status"],
        }

        body = "# Health Alert\n\n"
        body += f"**Status:** {report['overall_status']}\n\n"
        body += "## Issues\n\n"
        for issue in issues:
            body += f"- {issue}\n"

        ts = datetime.now().strftime("%H%M%S")
        alert_path = create_task_file(
            "Needs_Action", "ERROR", f"HEALTH_{ts}", metadata, body
        )

        log_error("Health alert created", alert_path.name, "health")
        return alert_path
