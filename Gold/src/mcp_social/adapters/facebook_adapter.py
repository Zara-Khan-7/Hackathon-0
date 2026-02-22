"""Facebook / Meta Graph API adapter.

Uses the facebook-sdk library for page posting and feed reading.
Falls back to mock data when FACEBOOK_MOCK=true.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger("social.facebook")


class FacebookAdapter:
    """Adapter for Facebook Graph API operations."""

    def __init__(self):
        self.mock = os.getenv("FACEBOOK_MOCK", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.page_token = os.getenv("FACEBOOK_PAGE_TOKEN", "")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID", "")
        self._api = None

    def _connect(self):
        if self.mock or self._api:
            return
        try:
            import facebook
            self._api = facebook.GraphAPI(access_token=self.page_token, version="3.1")
            logger.info("Connected to Facebook Graph API")
        except Exception as e:
            logger.error(f"Facebook connection failed: {e}, falling back to mock")
            self.mock = True

    def post_text(self, message: str) -> dict:
        """Post a text update to the Facebook page."""
        if self.mock or self.dry_run:
            logger.info(f"[{'DRY-RUN' if self.dry_run else 'MOCK'}] Facebook post: {message[:80]}...")
            return {
                "id": f"mock_fb_post_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "message": message,
                "status": "dry_run" if self.dry_run else "mock",
                "platform": "facebook",
            }

        self._connect()
        result = self._api.put_object(self.page_id, "feed", message=message)
        return {"id": result.get("id"), "message": message, "status": "posted", "platform": "facebook"}

    def get_page_feed(self, limit: int = 10) -> list[dict]:
        """Retrieve recent posts from the Facebook page."""
        if self.mock:
            from src.mcp_social.mock_social import MOCK_FACEBOOK_FEED
            return MOCK_FACEBOOK_FEED[:limit]

        self._connect()
        feed = self._api.get_connections(self.page_id, "feed", limit=limit)
        return feed.get("data", [])

    def get_notifications(self, limit: int = 10) -> list[dict]:
        """Get recent page notifications."""
        if self.mock:
            from src.mcp_social.mock_social import MOCK_FACEBOOK_NOTIFICATIONS
            return MOCK_FACEBOOK_NOTIFICATIONS[:limit]

        self._connect()
        notifs = self._api.get_connections("me", "notifications", limit=limit)
        return notifs.get("data", [])
