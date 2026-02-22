"""Instagram watcher — monitors DMs and mentions.

Uses the Instagram adapter for live mode, mock data for development.
Creates INSTAGRAM_*.md task files in Needs_Action/.
"""

import os
from typing import Any

from dotenv import load_dotenv

from src.watchers.base_watcher import BaseWatcher
from src.mcp_social.adapters.instagram_adapter import InstagramAdapter

load_dotenv()


class InstagramWatcher(BaseWatcher):
    """Watches Instagram for new DMs and mentions."""

    NAME = "instagram"
    PREFIX = "INSTAGRAM"
    DEST_FOLDER = "Needs_Action"

    def __init__(self, mock: bool = False, dry_run: bool = False, poll_interval: int = 600):
        self.adapter = InstagramAdapter()
        if mock:
            self.adapter.mock = True
        super().__init__(mock=mock, dry_run=dry_run, poll_interval=poll_interval)

    def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch DMs and mentions from Instagram."""
        if self.mock:
            from src.watchers.mock_data import MOCK_INSTAGRAM
            return MOCK_INSTAGRAM

        items = []
        dms = self.adapter.get_direct_messages(limit=10)
        for dm in dms:
            items.append({
                "id": dm.get("id", ""),
                "type": "dm",
                "from": dm.get("from", ""),
                "text": dm.get("text", ""),
                "timestamp": dm.get("timestamp", ""),
            })

        mentions = self.adapter.get_mentions(limit=10)
        for m in mentions:
            items.append({
                "id": m.get("id", ""),
                "type": "mention",
                "user": m.get("user", ""),
                "caption": m.get("caption", ""),
            })

        return items

    def item_to_task(self, item: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Convert an Instagram item to a task file."""
        item_id = item.get("id", "unknown")
        item_type = item.get("type", "notification")

        # Priority and approval classification
        if item_type == "dm":
            priority = "high"
            requires_approval = True
            sender = item.get("from", "unknown")
            subject = f"DM from {sender}"
        else:
            priority = "medium"
            requires_approval = True
            sender = item.get("user", "unknown")
            subject = f"Mentioned by {sender}"

        metadata = {
            "type": "instagram",
            "subtype": item_type,
            "priority": priority,
            "requires_approval": requires_approval,
            "platform": "instagram",
            "from": sender,
            "subject": subject,
        }

        body = f"# Instagram: {subject}\n\n"
        body += f"**Type:** {item_type}\n"
        body += f"**From:** {sender}\n\n"

        if item_type == "dm":
            body += f"## Message\n\n{item.get('text', '')}\n"
        else:
            body += f"## Mention\n\n{item.get('caption', '')}\n"

        return item_id, metadata, body


if __name__ == "__main__":
    InstagramWatcher.cli_main()
