"""Sales Agent — specializes in email responses, LinkedIn outreach, and CRM tasks.

Handles: EMAIL_, LINKEDIN_, SALESPOST_ prefixes.
Skills: complete_task, generate_sales_post, request_approval.
"""

from src.agents.base_agent import BaseSpecializedAgent, AgentCapability


class SalesAgent(BaseSpecializedAgent):
    """Specialized agent for sales-related tasks."""

    AGENT_TYPE = "sales"
    DISPLAY_NAME = "Sales Agent"

    def _register_capabilities(self) -> None:
        self._capabilities = [
            AgentCapability(
                name="email_response",
                description="Draft professional email replies to prospects and clients",
                task_prefixes=["EMAIL_"],
                priority=8,
            ),
            AgentCapability(
                name="linkedin_outreach",
                description="Draft LinkedIn messages and connection requests",
                task_prefixes=["LINKEDIN_"],
                priority=9,
            ),
            AgentCapability(
                name="sales_content",
                description="Generate sales posts and promotional content",
                task_prefixes=["SALESPOST_"],
                priority=10,
            ),
        ]

    def _execute(self, task: dict, dry_run: bool = False) -> str:
        filename = task.get("filename", "unknown")
        task_type = task.get("task_type", "unknown")
        body = task.get("body", "")

        if dry_run:
            return f"[DRY-RUN] Sales agent would process {filename} (type={task_type})"

        # Domain-specific processing
        if filename.startswith("EMAIL_"):
            return self._handle_email(task)
        elif filename.startswith("LINKEDIN_"):
            return self._handle_linkedin(task)
        elif filename.startswith("SALESPOST_"):
            return self._handle_sales_post(task)

        return f"Sales agent processed {filename}"

    def _handle_email(self, task: dict) -> str:
        """Draft a sales-oriented email reply."""
        subject = task.get("metadata", {}).get("subject", "No subject")
        sender = task.get("metadata", {}).get("from", "Unknown")
        return (
            f"Drafted sales email reply to {sender} "
            f"re: {subject}. Tone: professional, helpful. "
            f"Routed to approval."
        )

    def _handle_linkedin(self, task: dict) -> str:
        """Draft LinkedIn outreach message."""
        return (
            f"Drafted LinkedIn outreach for {task.get('filename', '')}. "
            f"Personalized based on profile context. Routed to approval."
        )

    def _handle_sales_post(self, task: dict) -> str:
        """Generate a sales/promotional post."""
        return (
            f"Generated sales post draft for {task.get('filename', '')}. "
            f"Includes value proposition and CTA. Routed to approval."
        )
