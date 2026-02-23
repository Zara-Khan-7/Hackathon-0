"""X / Twitter adapter using tweepy (API v2).

Handles tweet posting, mention tracking, and DM reading.
Falls back to mock data when TWITTER_MOCK=true.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger("social.twitter")


class TwitterAdapter:
    """Adapter for X/Twitter API v2 operations."""

    def __init__(self):
        self.mock = os.getenv("TWITTER_MOCK", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET", "")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
        self._client = None

    def _connect(self):
        if self.mock or self._client:
            return
        try:
            import tweepy
            self._client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
            )
            logger.info("Connected to X/Twitter API v2")
        except Exception as e:
            logger.error(f"Twitter connection failed: {e}, falling back to mock")
            self.mock = True

    def post_tweet(self, text: str) -> dict:
        """Post a tweet."""
        if self.mock or self.dry_run:
            logger.info(f"[{'DRY-RUN' if self.dry_run else 'MOCK'}] Tweet: {text[:80]}...")
            return {
                "id": f"mock_tweet_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "text": text,
                "status": "dry_run" if self.dry_run else "mock",
                "platform": "twitter",
            }

        self._connect()
        response = self._client.create_tweet(text=text)
        tweet_id = response.data["id"]
        return {"id": tweet_id, "text": text, "status": "posted", "platform": "twitter"}

    def get_mentions(self, limit: int = 10) -> list[dict]:
        """Get recent mentions of the authenticated user."""
        if self.mock:
            from src.mcp_social.mock_social import MOCK_TWITTER_MENTIONS
            return MOCK_TWITTER_MENTIONS[:limit]

        self._connect()
        me = self._client.get_me()
        mentions = self._client.get_users_mentions(
            me.data.id, max_results=min(limit, 100),
            tweet_fields=["created_at", "author_id", "text"]
        )
        if not mentions.data:
            return []
        return [
            {
                "id": str(t.id),
                "text": t.text,
                "author_id": str(t.author_id),
                "created_at": str(t.created_at),
            }
            for t in mentions.data
        ]

    def get_dms(self, limit: int = 10) -> list[dict]:
        """Get recent direct messages."""
        if self.mock:
            from src.mcp_social.mock_social import MOCK_TWITTER_DMS
            return MOCK_TWITTER_DMS[:limit]

        self._connect()
        # Note: DM access requires elevated API access
        try:
            events = self._client.get_direct_message_events(max_results=min(limit, 50))
            if not events.data:
                return []
            return [
                {
                    "id": str(e.id),
                    "text": e.text,
                    "sender_id": str(e.sender_id),
                    "created_at": str(e.created_at),
                }
                for e in events.data
            ]
        except Exception as e:
            logger.warning(f"Could not fetch DMs: {e}")
            return []
