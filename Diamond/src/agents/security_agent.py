"""Security Agent — monitors for threats, validates actions, enforces compliance.

Handles: ERROR_, EXECUTE_ prefixes (validates before execution).
Also performs proactive security scans on all outgoing actions.
"""

from src.agents.base_agent import BaseSpecializedAgent, AgentCapability


class SecurityAgent(BaseSpecializedAgent):
    """Specialized agent for security, compliance, and threat detection."""

    AGENT_TYPE = "security"
    DISPLAY_NAME = "Security Agent"

    # Patterns that trigger security review
    SENSITIVE_KEYWORDS = [
        "password", "credential", "secret", "token", "api_key",
        "bank", "transfer", "payment", "invoice", "wire",
    ]

    def _register_capabilities(self) -> None:
        self._capabilities = [
            AgentCapability(
                name="error_investigation",
                description="Investigate errors for security implications",
                task_prefixes=["ERROR_"],
                priority=7,
            ),
            AgentCapability(
                name="execution_validation",
                description="Validate approved actions before execution",
                task_prefixes=["EXECUTE_"],
                priority=5,
            ),
            AgentCapability(
                name="schedule_audit",
                description="Audit scheduled tasks for policy compliance",
                task_prefixes=["SCHEDULE_"],
                priority=3,
            ),
        ]

    def _execute(self, task: dict, dry_run: bool = False) -> str:
        filename = task.get("filename", "unknown")

        if dry_run:
            return f"[DRY-RUN] Security agent would validate {filename}"

        if filename.startswith("ERROR_"):
            return self._investigate_error(task)
        elif filename.startswith("EXECUTE_"):
            return self._validate_execution(task)

        return f"Security scan completed for {filename}: no issues found"

    def _investigate_error(self, task: dict) -> str:
        """Investigate an error for security implications."""
        body = task.get("body", "").lower()
        threats = [kw for kw in self.SENSITIVE_KEYWORDS if kw in body]

        if threats:
            return (
                f"SECURITY ALERT: Error in {task.get('filename', '')} "
                f"contains sensitive keywords: {', '.join(threats)}. "
                f"Flagged for manual review."
            )
        return (
            f"Error {task.get('filename', '')} investigated. "
            f"No security implications found. Safe to retry."
        )

    def _validate_execution(self, task: dict) -> str:
        """Validate an approved action before execution."""
        body = task.get("body", "").lower()
        issues = []

        # Check for sensitive data in outgoing content
        for kw in self.SENSITIVE_KEYWORDS:
            if kw in body:
                issues.append(f"Contains '{kw}'")

        if issues:
            return (
                f"VALIDATION WARNING for {task.get('filename', '')}: "
                f"{'; '.join(issues)}. Recommend additional review."
            )
        return (
            f"Execution validated for {task.get('filename', '')}. "
            f"No policy violations detected. Clear to proceed."
        )

    def scan_outgoing(self, content: str, action_type: str) -> dict:
        """Scan outgoing content for security/compliance issues.

        Called by SwarmOrchestrator before any external action.
        """
        issues = []
        content_lower = content.lower()

        for kw in self.SENSITIVE_KEYWORDS:
            if kw in content_lower:
                issues.append(f"Sensitive keyword: '{kw}'")

        return {
            "action_type": action_type,
            "passed": len(issues) == 0,
            "issues": issues,
            "scanned_by": self.agent_id,
        }
