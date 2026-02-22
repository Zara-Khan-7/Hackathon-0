"""Facebook watcher — monitors page notifications and messages.

Uses the Facebook adapter for live mode, mock data for development.
Creates FACEBOOK_*.md task files in Needs_Action/.
"""

import os
from typing import Any

from dotenv import load_dotenv

from src.watchers.base_watcher import BaseWatcher
from src.mcp_social.adapters.facebook_adapter import FacebookAdapter

load_dotenv()


class FacebookWatcher(BaseWatcher):
    """Watches Facebook page for new notifications and messages."""

    NAME = "facebook"
    PREFIX = "FACEBOOK"
    DEST_FOLDER = "Needs_Action"

    def __init__(self, mock: bool = False, dry_run: bool = False, poll_interval: int = 600):
        self.adapter = FacebookAdapter()
        if mock:
            self.adapter.mock = True
        super().__init__(mock=mock, dry_run=dry_run, poll_interval=poll_interval)

    def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch notifications and messages from Facebook."""
        if self.mock:
            from src.watchers.mock_data import MOCK_FACEBOOK
            return MOCK_FACEBOOK

        items = []
        notifications = self.adapter.get_notifications(limit=10)
        for n in notifications:
            items.append({
                "id": n.get("id", ""),
                "type": "notification",
                "title": n.get("title", ""),
                "message": n.get("message", ""),
                "created_time": n.get("created_time", ""),
                "unread": n.get("unread", False),
            })

        return items

    def item_to_task(self, item: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Convert a Facebook item to a task file."""
        item_id = item.get("id", "unknown")
        item_type = item.get("type", "notification")
        title = item.get("title", "Facebook notification")
        message = item.get("message", "")

        # Priority classification
        priority = "medium"
        requires_approval = False

        if item_type == "message" or "message" in title.lower():
            priority = "high"
            requires_approval = True
        elif "mention" in title.lower() or "tagged" in title.lower():
            priority = "high"
            requires_approval = True
        elif "comment" in title.lower():
            priority = "medium"

        metadata = {
            "type": "facebook",
            "subtype": item_type,
            "priority": priority,
            "requires_approval": requires_approval,
            "platform": "facebook",
            "from": title.split(" ")[0] if title else "Facebook",
            "subject": title,
        }

        body = f"# Facebook: {title}\n\n"
        body += f"**Type:** {item_type}\n"
        body += f"**Time:** {item.get('created_time', 'N/A')}\n\n"
        if message:
            body += f"## Content\n\n{message}\n"

        return item_id, metadata, body


if __name__ == "__main__":
    FacebookWatcher.cli_main()
