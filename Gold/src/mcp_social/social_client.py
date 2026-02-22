"""
Helper wrapper for calling the Social MCP server as a subprocess.

Usage:
    from src.mcp_social.social_client import SocialClient
    client = SocialClient()
    summary = client.get_social_summary(platform="all")
"""

import json
import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger("social_client")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class SocialClient:
    """Client wrapper that spawns the Social MCP server as a subprocess."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.server_module = "src.mcp_social.social_server"

    def call_mcp_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Call an MCP tool on the Social server via subprocess."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": tool_name, "arguments": arguments or {}},
        }
        request_json = json.dumps(request) + "\n"

        try:
            proc = subprocess.run(
                [sys.executable, "-m", self.server_module],
                input=request_json,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(PROJECT_ROOT),
            )
            for line in proc.stdout.strip().split("\n"):
                if line.strip():
                    response = json.loads(line)
                    if "result" in response:
                        content = response["result"].get("content", [])
                        if content:
                            return json.loads(content[0].get("text", "{}"))
                    elif "error" in response:
                        return {"error": response["error"].get("message", "Unknown error")}
            return {"error": "No valid response from Social MCP server"}
        except subprocess.TimeoutExpired:
            return {"error": f"Social MCP server timed out after {self.timeout}s"}
        except Exception as e:
            return {"error": f"Social MCP client error: {e}"}

    def post_facebook(self, message: str) -> dict:
        return self.call_mcp_tool("post_facebook", {"message": message})

    def post_instagram(self, caption: str, image_path: str = None) -> dict:
        args = {"caption": caption}
        if image_path:
            args["image_path"] = image_path
        return self.call_mcp_tool("post_instagram", args)

    def post_twitter(self, text: str) -> dict:
        return self.call_mcp_tool("post_twitter", {"text": text})

    def get_social_summary(self, platform: str = "all", limit: int = 5) -> dict:
        return self.call_mcp_tool("get_social_summary", {"platform": platform, "limit": limit})

    def draft_social_post(self, platform: str, content: str, notes: str = "") -> dict:
        args = {"platform": platform, "content": content}
        if notes:
            args["notes"] = notes
        return self.call_mcp_tool("draft_social_post", args)
