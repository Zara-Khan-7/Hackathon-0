"""MCP Email Server — JSON-RPC over stdio.

Provides tools: send_email, draft_email, list_drafts.
Dry-run by default (logs to Logs/ instead of actually sending).

Protocol: JSON-RPC 2.0 over stdin/stdout (MCP standard).
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_ops import get_folder
from src.utils.logger import log_action, log_error

load_dotenv(project_root / ".env")


# === Configuration ===

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)


# === Tool Definitions ===

TOOLS = [
    {
        "name": "send_email",
        "description": "Send an email. In dry-run mode, logs the email instead of sending.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body (plain text)"},
                "cc": {"type": "string", "description": "CC recipients (comma-separated)", "default": ""},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "draft_email",
        "description": "Create an email draft saved to Logs/drafts/. Does not send.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body (plain text)"},
                "cc": {"type": "string", "description": "CC recipients (comma-separated)", "default": ""},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "list_drafts",
        "description": "List all saved email drafts.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# === Tool Handlers ===

def handle_send_email(args: dict) -> dict:
    """Send an email or log it in dry-run mode."""
    to = args["to"]
    subject = args["subject"]
    body = args["body"]
    cc = args.get("cc", "")

    if DRY_RUN:
        # Log to file instead of sending
        log_dir = get_folder("Logs")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        log_file = log_dir / f"email_dryrun_{timestamp}.md"

        content = (
            f"# Email (DRY-RUN)\n\n"
            f"**To:** {to}\n"
            f"**CC:** {cc}\n"
            f"**Subject:** {subject}\n"
            f"**From:** {EMAIL_FROM}\n"
            f"**Timestamp:** {timestamp}\n\n"
            f"## Body\n\n{body}\n"
        )
        log_file.write_text(content, encoding="utf-8")
        log_action("DRY-RUN email logged", f"To: {to}, Subject: {subject}", "mcp_email")

        return {
            "content": [{"type": "text", "text": f"[DRY-RUN] Email logged to {log_file.name}. To: {to}, Subject: {subject}"}],
            "isError": False,
        }

    # Live mode — actually send
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        msg.attach(MIMEText(body, "plain"))

        recipients = [to] + [c.strip() for c in cc.split(",") if c.strip()]

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())

        log_action("Email sent", f"To: {to}, Subject: {subject}", "mcp_email")

        return {
            "content": [{"type": "text", "text": f"Email sent successfully. To: {to}, Subject: {subject}"}],
            "isError": False,
        }

    except Exception as e:
        log_error("Email send failed", str(e), "mcp_email")
        return {
            "content": [{"type": "text", "text": f"Error sending email: {str(e)}"}],
            "isError": True,
        }


def handle_draft_email(args: dict) -> dict:
    """Save an email draft to Logs/drafts/."""
    to = args["to"]
    subject = args["subject"]
    body = args["body"]
    cc = args.get("cc", "")

    drafts_dir = get_folder("Logs") / "drafts"
    drafts_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_subject = "".join(c if c.isalnum() or c in "-_ " else "" for c in subject)[:50]
    draft_file = drafts_dir / f"draft_{timestamp}_{safe_subject}.md"

    content = (
        f"---\n"
        f"type: email_draft\n"
        f"to: \"{to}\"\n"
        f"cc: \"{cc}\"\n"
        f"subject: \"{subject}\"\n"
        f"from: \"{EMAIL_FROM}\"\n"
        f"created: \"{timestamp}\"\n"
        f"status: draft\n"
        f"---\n\n"
        f"# Email Draft: {subject}\n\n"
        f"**To:** {to}\n"
        f"**CC:** {cc}\n"
        f"**Subject:** {subject}\n\n"
        f"## Body\n\n{body}\n"
    )
    draft_file.write_text(content, encoding="utf-8")
    log_action("Draft saved", f"To: {to}, Subject: {subject}", "mcp_email")

    return {
        "content": [{"type": "text", "text": f"Draft saved: {draft_file.name}"}],
        "isError": False,
    }


def handle_list_drafts(args: dict) -> dict:
    """List all saved email drafts."""
    drafts_dir = get_folder("Logs") / "drafts"
    if not drafts_dir.exists():
        return {
            "content": [{"type": "text", "text": "No drafts found."}],
            "isError": False,
        }

    drafts = sorted(drafts_dir.glob("draft_*.md"))
    if not drafts:
        return {
            "content": [{"type": "text", "text": "No drafts found."}],
            "isError": False,
        }

    lines = [f"Found {len(drafts)} draft(s):\n"]
    for d in drafts:
        lines.append(f"- {d.name}")

    return {
        "content": [{"type": "text", "text": "\n".join(lines)}],
        "isError": False,
    }


TOOL_HANDLERS = {
    "send_email": handle_send_email,
    "draft_email": handle_draft_email,
    "list_drafts": handle_list_drafts,
}


# === JSON-RPC Server ===

def handle_request(request: dict) -> dict:
    """Process a single JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "ai-employee-email",
                    "version": "1.0.0",
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }

        result = handler(arguments)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # Notifications (no id) — acknowledge silently
    if req_id is None:
        return None

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def main():
    """Main loop — read JSON-RPC requests from stdin, write responses to stdout."""
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
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
