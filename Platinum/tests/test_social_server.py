"""Tests for the unified Social MCP server."""

import json
import pytest
import os

os.environ["FACEBOOK_MOCK"] = "true"
os.environ["INSTAGRAM_MOCK"] = "true"
os.environ["TWITTER_MOCK"] = "true"
os.environ["DRY_RUN"] = "true"

from src.mcp_social.social_server import handle_request, TOOLS
from src.mcp_social.adapters.facebook_adapter import FacebookAdapter
from src.mcp_social.adapters.instagram_adapter import InstagramAdapter
from src.mcp_social.adapters.twitter_adapter import TwitterAdapter


class TestAdapters:
    """Test individual platform adapters in mock mode."""

    def test_facebook_post_text_mock(self):
        adapter = FacebookAdapter()
        adapter.mock = True
        result = adapter.post_text("Hello world")
        assert result["platform"] == "facebook"
        assert result["message"] == "Hello world"

    def test_facebook_get_feed(self):
        adapter = FacebookAdapter()
        adapter.mock = True
        feed = adapter.get_page_feed(limit=3)
        assert len(feed) <= 3
        assert all("id" in p for p in feed)

    def test_instagram_post_caption_mock(self):
        adapter = InstagramAdapter()
        adapter.mock = True
        result = adapter.post_caption("Test caption")
        assert result["platform"] == "instagram"
        assert result["caption"] == "Test caption"

    def test_instagram_get_dms(self):
        adapter = InstagramAdapter()
        adapter.mock = True
        dms = adapter.get_direct_messages(limit=5)
        assert isinstance(dms, list)

    def test_twitter_post_tweet_mock(self):
        adapter = TwitterAdapter()
        adapter.mock = True
        result = adapter.post_tweet("Test tweet")
        assert result["platform"] == "twitter"
        assert result["text"] == "Test tweet"

    def test_twitter_get_mentions(self):
        adapter = TwitterAdapter()
        adapter.mock = True
        mentions = adapter.get_mentions(limit=5)
        assert isinstance(mentions, list)


class TestSocialMCPProtocol:
    """Test JSON-RPC protocol handling for the social server."""

    def test_initialize(self):
        request = {"jsonrpc": "2.0", "method": "initialize", "id": 1}
        response = handle_request(request)
        assert response["result"]["serverInfo"]["name"] == "ai-employee-social"

    def test_tools_list(self):
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        response = handle_request(request)
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "post_facebook" in tool_names
        assert "post_instagram" in tool_names
        assert "post_twitter" in tool_names
        assert "get_social_summary" in tool_names
        assert "draft_social_post" in tool_names

    def test_post_facebook_call(self):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "post_facebook", "arguments": {"message": "Test post"}},
        }
        response = handle_request(request)
        assert not response["result"]["isError"]
        data = json.loads(response["result"]["content"][0]["text"])
        assert data["platform"] == "facebook"

    def test_post_twitter_call(self):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "post_twitter", "arguments": {"text": "Test tweet"}},
        }
        response = handle_request(request)
        assert not response["result"]["isError"]
        data = json.loads(response["result"]["content"][0]["text"])
        assert data["platform"] == "twitter"

    def test_get_social_summary_all(self):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "get_social_summary", "arguments": {"platform": "all"}},
        }
        response = handle_request(request)
        assert not response["result"]["isError"]
        data = json.loads(response["result"]["content"][0]["text"])
        assert "facebook" in data
        assert "instagram" in data
        assert "twitter" in data

    def test_unknown_tool(self):
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": "nonexistent", "arguments": {}},
        }
        response = handle_request(request)
        assert "error" in response
