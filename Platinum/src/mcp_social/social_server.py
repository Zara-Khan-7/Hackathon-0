"""
Unified MCP JSON-RPC server for Facebook, Instagram, and X/Twitter.

Routes tool calls to the appropriate platform adapter based on the `platform`
argument. Supports mock mode for all three platforms.

Usage:
    echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m src.mcp_social.social_server
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("mcp_social")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

from src.mcp_social.adapters.facebook_adapter import FacebookAdapter
from src.mcp_social.adapters.instagram_adapter import InstagramAdapter
from src.mcp_social.adapters.twitter_adapter import TwitterAdapter

# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

ADAPTERS = {
    "facebook": FacebookAdapter,
    "instagram": InstagramAdapter,
    "twitter": TwitterAdapter,
}

_adapter_instances: dict = {}


def _get_adapter(platform: str):
    """Get or create a platform adapter instance."""
    if platform not in _adapter_instances:
        cls = ADAPTERS.get(platform)
        if not cls:
            raise ValueError(f"Unknown platform: {platform}. Must be one of: {list(ADAPTERS.keys())}")
        _adapter_instances[platform] = cls()
    return _adapter_instances[platform]


# ---------------------------------------------------------------------------
# MCP Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "post_facebook",
        "description": "Post a text update to the Facebook page. REQUIRES prior HITL approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The post content"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "post_instagram",
        "description": "Post to Instagram with caption (photo post or caption draft). REQUIRES prior HITL approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "caption": {"type": "string", "description": "The post caption"},
                "image_path": {"type": "string", "description": "Optional path to image file"},
            },
            "required": ["caption"],
        },
    },
    {
        "name": "post_twitter",
        "description": "Post a tweet to X/Twitter. REQUIRES prior HITL approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The tweet text (max 280 chars)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "get_social_summary",
        "description": "Get a summary of recent activity across one or all social platforms.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["facebook", "instagram", "twitter", "all"],
                    "default": "all",
                    "description": "Which platform(s) to summarize",
                },
                "limit": {"type": "integer", "default": 5, "description": "Max items per section"},
            },
        },
    },
    {
        "name": "draft_social_post",
        "description": "Draft a post for a specific platform without publishing. Saved to Logs/drafts/.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["facebook", "instagram", "twitter"],
                    "description": "Target platform",
                },
                "content": {"type": "string", "description": "The post content/caption/tweet"},
                "notes": {"type": "string", "description": "Optional notes about the draft"},
            },
            "required": ["platform", "content"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _handle_post_facebook(args: dict) -> dict:
    adapter = _get_adapter("facebook")
    return adapter.post_text(args["message"])


def _handle_post_instagram(args: dict) -> dict:
    adapter = _get_adapter("instagram")
    if args.get("image_path"):
        return adapter.post_photo(args["image_path"], args["caption"])
    return adapter.post_caption(args["caption"])


def _handle_post_twitter(args: dict) -> dict:
    adapter = _get_adapter("twitter")
    return adapter.post_tweet(args["text"])


def _handle_get_social_summary(args: dict) -> dict:
    platform = args.get("platform", "all")
    limit = args.get("limit", 5)
    summary = {}

    platforms = ["facebook", "instagram", "twitter"] if platform == "all" else [platform]

    for p in platforms:
        adapter = _get_adapter(p)
        section = {}

        if p == "facebook":
            section["feed"] = adapter.get_page_feed(limit)
            section["notifications"] = adapter.get_notifications(limit)
        elif p == "instagram":
            section["dms"] = adapter.get_direct_messages(limit)
            section["mentions"] = adapter.get_mentions(limit)
        elif p == "twitter":
            section["mentions"] = adapter.get_mentions(limit)
            section["dms"] = adapter.get_dms(limit)

        summary[p] = section

    return summary


def _handle_draft_social_post(args: dict) -> dict:
    from src.utils.file_ops import get_folder

    platform = args["platform"]
    content = args["content"]
    notes = args.get("notes", "")

    drafts_dir = get_folder("Logs") / "drafts"
    drafts_dir.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_file = drafts_dir / f"draft_{platform}_{ts}.md"

    body = f"# Social Media Draft — {platform.title()}\n\n"
    body += f"**Platform:** {platform}\n"
    body += f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    body += f"## Content\n\n{content}\n"
    if notes:
        body += f"\n## Notes\n\n{notes}\n"

    draft_file.write_text(body, encoding="utf-8")
    logger.info(f"Draft saved: {draft_file}")

    return {
        "draft_file": str(draft_file),
        "platform": platform,
        "content": content,
        "status": "drafted",
    }


TOOL_HANDLERS = {
    "post_facebook": _handle_post_facebook,
    "post_instagram": _handle_post_instagram,
    "post_twitter": _handle_post_twitter,
    "get_social_summary": _handle_get_social_summary,
    "draft_social_post": _handle_draft_social_post,
}

# ---------------------------------------------------------------------------
# JSON-RPC request handling
# ---------------------------------------------------------------------------

def handle_request(request: dict) -> dict:
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ai-employee-social", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)

        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
            }

        try:
            result = handler(arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, default=str)}],
                    "isError": False,
                },
            }
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


# ---------------------------------------------------------------------------
# Main: stdio JSON-RPC loop
# ---------------------------------------------------------------------------

def main():
    logger.info("Social MCP server started (reading from stdin)")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
