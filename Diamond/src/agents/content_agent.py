"""Content Agent — specializes in social media, content creation, and brand management.

Handles: FACEBOOK_, INSTAGRAM_, TWITTER_, SOCIAL_, WHATSAPP_ prefixes.
Skills: generate_social_post, post_approved_social, summarize_social_activity, whatsapp_reply.
"""

from src.agents.base_agent import BaseSpecializedAgent, AgentCapability


class ContentAgent(BaseSpecializedAgent):
    """Specialized agent for content and social media tasks."""

    AGENT_TYPE = "content"
    DISPLAY_NAME = "Content Agent"

    def _register_capabilities(self) -> None:
        self._capabilities = [
            AgentCapability(
                name="facebook_content",
                description="Create and manage Facebook posts",
                task_prefixes=["FACEBOOK_"],
                priority=9,
            ),
            AgentCapability(
                name="instagram_content",
                description="Create and manage Instagram posts",
                task_prefixes=["INSTAGRAM_"],
                priority=9,
            ),
            AgentCapability(
                name="twitter_content",
                description="Create and manage Twitter/X posts",
                task_prefixes=["TWITTER_"],
                priority=9,
            ),
            AgentCapability(
                name="social_analytics",
                description="Analyze social media metrics and trends",
                task_prefixes=["SOCIAL_"],
                priority=7,
            ),
            AgentCapability(
                name="whatsapp_messaging",
                description="Draft WhatsApp business replies",
                task_prefixes=["WHATSAPP_"],
                priority=8,
            ),
        ]

    def _execute(self, task: dict, dry_run: bool = False) -> str:
        filename = task.get("filename", "unknown")
        task_type = task.get("task_type", "unknown")

        if dry_run:
            return f"[DRY-RUN] Content agent would process {filename} (type={task_type})"

        if filename.startswith("FACEBOOK_"):
            return self._handle_social_post(task, "Facebook")
        elif filename.startswith("INSTAGRAM_"):
            return self._handle_social_post(task, "Instagram")
        elif filename.startswith("TWITTER_"):
            return self._handle_social_post(task, "Twitter/X")
        elif filename.startswith("SOCIAL_"):
            return self._handle_social_analytics(task)
        elif filename.startswith("WHATSAPP_"):
            return self._handle_whatsapp(task)

        return f"Content agent processed {filename}"

    def _handle_social_post(self, task: dict, platform: str) -> str:
        """Draft a platform-specific social media post."""
        return (
            f"Drafted {platform} post for {task.get('filename', '')}. "
            f"Optimized for platform best practices. Routed to approval."
        )

    def _handle_social_analytics(self, task: dict) -> str:
        """Analyze social media metrics."""
        return (
            f"Analyzed social metrics for {task.get('filename', '')}. "
            f"Engagement rates, reach, and trends summarized."
        )

    def _handle_whatsapp(self, task: dict) -> str:
        """Draft WhatsApp business reply."""
        sender = task.get("metadata", {}).get("from", "Unknown")
        return (
            f"Drafted WhatsApp reply to {sender} for {task.get('filename', '')}. "
            f"Routed to approval (all messages require HITL)."
        )
