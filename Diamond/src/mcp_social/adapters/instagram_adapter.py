"""Instagram adapter using instagrapi (or mock fallback).

Handles photo posting, caption posting, DM reading, and mention tracking.
Falls back to mock data when INSTAGRAM_MOCK=true or instagrapi unavailable.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger("social.instagram")


class InstagramAdapter:
    """Adapter for Instagram API operations."""

    def __init__(self):
        self.mock = os.getenv("INSTAGRAM_MOCK", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.username = os.getenv("INSTAGRAM_USERNAME", "")
        self.password = os.getenv("INSTAGRAM_PASSWORD", "")
        self._client = None

    def _connect(self):
        if self.mock or self._client:
            return
        try:
            from instagrapi import Client
            self._client = Client()
            self._client.login(self.username, self.password)
            logger.info("Connected to Instagram via instagrapi")
        except Exception as e:
            logger.error(f"Instagram connection failed: {e}, falling back to mock")
            self.mock = True

    def post_photo(self, image_path: str, caption: str) -> dict:
        """Post a photo with caption to Instagram."""
        if self.mock or self.dry_run:
            logger.info(f"[{'DRY-RUN' if self.dry_run else 'MOCK'}] Instagram photo: {caption[:80]}...")
            return {
                "id": f"mock_ig_post_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "caption": caption,
                "status": "dry_run" if self.dry_run else "mock",
                "platform": "instagram",
            }

        self._connect()
        media = self._client.photo_upload(image_path, caption)
        return {"id": str(media.pk), "caption": caption, "status": "posted", "platform": "instagram"}

    def post_caption(self, caption: str) -> dict:
        """Create a text-based post (story or caption-only post)."""
        if self.mock or self.dry_run:
            logger.info(f"[{'DRY-RUN' if self.dry_run else 'MOCK'}] Instagram caption: {caption[:80]}...")
            return {
                "id": f"mock_ig_caption_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "caption": caption,
                "status": "dry_run" if self.dry_run else "mock",
                "platform": "instagram",
            }

        self._connect()
        # Note: Instagram requires an image for feed posts; this drafts a caption
        return {"id": "draft", "caption": caption, "status": "draft", "platform": "instagram"}

    def get_direct_messages(self, limit: int = 10) -> list[dict]:
        """Retrieve recent direct messages."""
        if self.mock:
            from src.mcp_social.mock_social import MOCK_INSTAGRAM_DMS
            return MOCK_INSTAGRAM_DMS[:limit]

        self._connect()
        threads = self._client.direct_threads(amount=limit)
        results = []
        for thread in threads:
            for msg in thread.messages[:1]:
                results.append({
                    "id": str(msg.id),
                    "from": thread.thread_title,
                    "text": msg.text or "(media)",
                    "timestamp": str(msg.timestamp),
                })
        return results[:limit]

    def get_mentions(self, limit: int = 10) -> list[dict]:
        """Get recent mentions/tags."""
        if self.mock:
            from src.mcp_social.mock_social import MOCK_INSTAGRAM_MENTIONS
            return MOCK_INSTAGRAM_MENTIONS[:limit]

        self._connect()
        # instagrapi doesn't have a direct mentions endpoint; use usertag_medias
        try:
            user_id = self._client.user_id
            medias = self._client.usertag_medias(user_id, amount=limit)
            return [
                {"id": str(m.pk), "user": m.user.username, "caption": m.caption_text[:100]}
                for m in medias
            ]
        except Exception as e:
            logger.warning(f"Could not fetch mentions: {e}")
            return []
