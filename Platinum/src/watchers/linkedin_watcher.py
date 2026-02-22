"""LinkedIn watcher — monitors LinkedIn for new messages, connection requests, and engagement.

Uses Playwright for browser automation in live mode, mock data for testing.
"""

import os
from typing import Any

from dotenv import load_dotenv

from src.watchers.base_watcher import BaseWatcher
from src.watchers.mock_data import MOCK_LINKEDIN_ITEMS
from src.utils.logger import log_action, log_error

load_dotenv()


class LinkedInWatcher(BaseWatcher):
    NAME = "linkedin"
    PREFIX = "LINKEDIN"
    DEST_FOLDER = "Needs_Action"

    def __init__(self, **kwargs):
        interval = int(os.getenv("LINKEDIN_POLL_INTERVAL", "3600"))
        kwargs.setdefault("poll_interval", interval)
        super().__init__(**kwargs)
        self._browser = None
        self._page = None

    def _init_browser(self):
        """Initialize Playwright browser (lazy)."""
        if self._page is not None:
            return

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._page = self._browser.new_page()

            # Login to LinkedIn
            email = os.getenv("LINKEDIN_EMAIL", "")
            password = os.getenv("LINKEDIN_PASSWORD", "")

            if not email or not password:
                raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")

            self._page.goto("https://www.linkedin.com/login")
            self._page.fill("#username", email)
            self._page.fill("#password", password)
            self._page.click('button[type="submit"]')
            self._page.wait_for_load_state("networkidle")

            log_action("LinkedIn watcher", "Browser logged in", self.NAME)

        except Exception as e:
            log_error("LinkedIn browser init failed", str(e), self.NAME)
            raise

    def _fetch_real_items(self) -> list[dict[str, Any]]:
        """Fetch LinkedIn items via browser automation."""
        self._init_browser()
        items = []

        try:
            # Check messages
            self._page.goto("https://www.linkedin.com/messaging/")
            self._page.wait_for_load_state("networkidle")

            conversations = self._page.query_selector_all(".msg-conversation-listitem")
            for conv in conversations[:5]:
                name_el = conv.query_selector(".msg-conversation-listitem__participant-names")
                preview_el = conv.query_selector(".msg-conversation-card__message-snippet")

                if name_el and preview_el:
                    items.append({
                        "id": f"li_msg_{hash(name_el.inner_text())}",
                        "type": "message",
                        "from_name": name_el.inner_text().strip(),
                        "from_title": "",
                        "message": preview_el.inner_text().strip(),
                        "date": "",
                    })

            # Check notifications
            self._page.goto("https://www.linkedin.com/notifications/")
            self._page.wait_for_load_state("networkidle")

            notifs = self._page.query_selector_all(".nt-card")
            for notif in notifs[:5]:
                text_el = notif.query_selector(".nt-card__text")
                if text_el:
                    text = text_el.inner_text().strip()
                    if "connection" in text.lower():
                        items.append({
                            "id": f"li_conn_{hash(text)}",
                            "type": "connection_request",
                            "from_name": text.split(" ")[0],
                            "from_title": "",
                            "message": text,
                            "date": "",
                        })

        except Exception as e:
            log_error("LinkedIn scrape failed", str(e), self.NAME)

        return items

    def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch LinkedIn items — mock or real."""
        if self.mock:
            log_action("LinkedIn watcher", "Using mock data", self.NAME)
            return MOCK_LINKEDIN_ITEMS
        return self._fetch_real_items()

    def _classify_priority(self, item: dict[str, Any]) -> str:
        """Classify priority based on item type and content."""
        item_type = item.get("type", "")
        message = item.get("message", "").lower()

        if item_type == "message" and any(kw in message for kw in ["help", "hire", "project", "interested"]):
            return "high"
        if item_type == "connection_request":
            return "medium"
        if item_type == "engagement":
            likes = item.get("likes", 0)
            return "high" if likes > 100 else "medium"
        return "low"

    def item_to_task(self, item: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Convert LinkedIn item to task file components."""
        item_type = item.get("type", "unknown")
        priority = self._classify_priority(item)

        name = item.get("id", "unknown")
        metadata = {
            "type": "linkedin",
            "subtype": item_type,
            "priority": priority,
            "from": item.get("from_name", ""),
            "date": item.get("date", ""),
            "status": "pending",
            "requires_approval": item_type in ("message", "connection_request"),
        }

        if item_type == "connection_request":
            body = f"# LinkedIn: Connection Request\n\n"
            body += f"**From:** {item.get('from_name', '')} — {item.get('from_title', '')}\n"
            body += f"**Date:** {item.get('date', '')}\n"
            body += f"**Priority:** {priority}\n\n"
            body += f"## Message\n\n{item.get('message', '')}\n"

        elif item_type == "message":
            body = f"# LinkedIn: Direct Message\n\n"
            body += f"**From:** {item.get('from_name', '')} — {item.get('from_title', '')}\n"
            body += f"**Date:** {item.get('date', '')}\n"
            body += f"**Priority:** {priority}\n\n"
            body += f"## Message\n\n{item.get('message', '')}\n"

        elif item_type == "engagement":
            metadata["requires_approval"] = False
            body = f"# LinkedIn: Post Engagement Update\n\n"
            body += f"**Post:** {item.get('post_title', '')}\n"
            body += f"**Date:** {item.get('date', '')}\n"
            body += f"**Priority:** {priority}\n\n"
            body += f"## Stats\n\n"
            body += f"- Likes: {item.get('likes', 0)}\n"
            body += f"- Comments: {item.get('comments', 0)}\n"
            body += f"- Shares: {item.get('shares', 0)}\n\n"
            body += f"## Top Comment\n\n{item.get('top_comment', '')}\n"

        else:
            body = f"# LinkedIn: {item_type}\n\n{item}\n"

        return name, metadata, body


if __name__ == "__main__":
    LinkedInWatcher.cli_main()
