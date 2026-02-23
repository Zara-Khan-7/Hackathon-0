"""Twitter / X watcher — monitors mentions and DMs.

Uses the Twitter adapter for live mode, mock data for development.
Creates TWITTER_*.md task files in Needs_Action/.
"""

import os
from typing import Any

from dotenv import load_dotenv

from src.watchers.base_watcher import BaseWatcher
from src.mcp_social.adapters.twitter_adapter import TwitterAdapter

load_dotenv()


class TwitterWatcher(BaseWatcher):
    """Watches X/Twitter for new mentions and DMs."""

    NAME = "twitter"
    PREFIX = "TWITTER"
    DEST_FOLDER = "Needs_Action"

    def __init__(self, mock: bool = False, dry_run: bool = False, poll_interval: int = 300):
        self.adapter = TwitterAdapter()
        if mock:
            self.adapter.mock = True
        super().__init__(mock=mock, dry_run=dry_run, poll_interval=poll_interval)

    def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch mentions and DMs from Twitter/X."""
        if self.mock:
            from src.watchers.mock_data import MOCK_TWITTER
            return MOCK_TWITTER

        items = []
        mentions = self.adapter.get_mentions(limit=10)
        for m in mentions:
            items.append({
                "id": m.get("id", ""),
                "type": "mention",
                "text": m.get("text", ""),
                "author_id": m.get("author_id", ""),
                "author_name": m.get("author_name", ""),
                "created_at": m.get("created_at", ""),
            })

        dms = self.adapter.get_dms(limit=10)
        for dm in dms:
            items.append({
                "id": dm.get("id", ""),
                "type": "dm",
                "text": dm.get("text", ""),
                "sender_id": dm.get("sender_id", ""),
                "sender_name": dm.get("sender_name", ""),
                "created_at": dm.get("created_at", ""),
            })

        return items

    def item_to_task(self, item: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Convert a Twitter item to a task file."""
        item_id = item.get("id", "unknown")
        item_type = item.get("type", "mention")
        text = item.get("text", "")

        if item_type == "dm":
            sender = item.get("sender_name", item.get("sender_id", "unknown"))
            priority = "high"
            requires_approval = True
            subject = f"DM from {sender}"
        else:
            sender = item.get("author_name", item.get("author_id", "unknown"))
            # High priority if it's a question or business inquiry
            business_keywords = ["partnership", "interested", "pricing", "demo", "hire", "collab"]
            is_business = any(kw in text.lower() for kw in business_keywords)
            priority = "high" if is_business else "medium"
            requires_approval = is_business
            subject = f"Mention by {sender}"

        metadata = {
            "type": "twitter",
            "subtype": item_type,
            "priority": priority,
            "requires_approval": requires_approval,
            "platform": "twitter",
            "from": sender,
            "subject": subject,
        }

        body = f"# Twitter: {subject}\n\n"
        body += f"**Type:** {item_type}\n"
        body += f"**From:** {sender}\n"
        body += f"**Time:** {item.get('created_at', 'N/A')}\n\n"
        body += f"## Content\n\n{text}\n"

        return item_id, metadata, body


if __name__ == "__main__":
    TwitterWatcher.cli_main()
