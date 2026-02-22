"""Gmail watcher — polls Gmail API for new emails, creates task files in Needs_Action/.

Supports --mock mode using fake data for testing without credentials.
"""

import base64
import os
from typing import Any

from dotenv import load_dotenv

from src.watchers.base_watcher import BaseWatcher
from src.watchers.mock_data import MOCK_EMAILS
from src.utils.logger import log_action, log_error

load_dotenv()


class GmailWatcher(BaseWatcher):
    NAME = "gmail"
    PREFIX = "EMAIL"
    DEST_FOLDER = "Needs_Action"

    def __init__(self, **kwargs):
        interval = int(os.getenv("GMAIL_POLL_INTERVAL", "300"))
        kwargs.setdefault("poll_interval", interval)
        super().__init__(**kwargs)
        self._service = None

    def _get_gmail_service(self):
        """Build Gmail API service (lazy init)."""
        if self._service is not None:
            return self._service

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
            creds = None
            token_path = os.getenv("GMAIL_TOKEN_JSON", "token.json")
            creds_path = os.getenv("GMAIL_CREDENTIALS_JSON", "credentials.json")

            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(token_path, "w") as f:
                    f.write(creds.to_json())

            self._service = build("gmail", "v1", credentials=creds)
            return self._service

        except Exception as e:
            log_error("Gmail API init failed", str(e), self.NAME)
            raise

    def _fetch_real_emails(self) -> list[dict[str, Any]]:
        """Fetch emails from Gmail API."""
        service = self._get_gmail_service()
        label = os.getenv("GMAIL_WATCH_LABEL", "INBOX")

        results = service.users().messages().list(
            userId="me", labelIds=[label], q="is:unread", maxResults=10
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

            # Extract body
            body = ""
            payload = msg["payload"]
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain" and "data" in part.get("body", {}):
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break
            elif "body" in payload and "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

            emails.append({
                "id": msg_ref["id"],
                "from": headers.get("From", "unknown"),
                "subject": headers.get("Subject", "(no subject)"),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
                "body": body,
                "labels": msg.get("labelIds", []),
            })

        return emails

    def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch emails — mock or real."""
        if self.mock:
            log_action("Gmail watcher", "Using mock data", self.NAME)
            return MOCK_EMAILS
        return self._fetch_real_emails()

    def _classify_priority(self, email: dict[str, Any]) -> str:
        """Simple priority classification based on content."""
        subject = email.get("subject", "").lower()
        sender = email.get("from", "").lower()
        body = email.get("body", "").lower()

        # High priority: invoices, urgent, money
        high_keywords = ["invoice", "payment", "urgent", "asap", "deadline", "overdue"]
        if any(kw in subject or kw in body for kw in high_keywords):
            return "high"

        # Low priority: newsletters, automated
        low_keywords = ["newsletter", "digest", "unsubscribe", "no-reply", "noreply"]
        if any(kw in subject or kw in sender or kw in body for kw in low_keywords):
            return "low"

        return "medium"

    def _classify_type(self, email: dict[str, Any]) -> str:
        """Classify the email type for routing."""
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()

        if any(kw in subject or kw in body for kw in ["invoice", "payment", "billing"]):
            return "financial"
        if any(kw in subject or kw in body for kw in ["partner", "opportunity", "collaborate"]):
            return "business_development"
        if any(kw in subject or kw in body for kw in ["newsletter", "digest", "weekly"]):
            return "newsletter"
        return "general"

    def item_to_task(self, item: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Convert email to task file components."""
        priority = self._classify_priority(item)
        email_type = self._classify_type(item)

        name = item.get("id", "unknown")
        metadata = {
            "type": "email",
            "subtype": email_type,
            "priority": priority,
            "from": item.get("from", "unknown"),
            "subject": item.get("subject", "(no subject)"),
            "date": item.get("date", ""),
            "status": "pending",
            "requires_approval": email_type in ("financial", "business_development"),
        }

        body = f"# Email: {item.get('subject', '(no subject)')}\n\n"
        body += f"**From:** {item.get('from', 'unknown')}\n"
        body += f"**Date:** {item.get('date', '')}\n"
        body += f"**Priority:** {priority}\n"
        body += f"**Type:** {email_type}\n\n"
        body += f"## Content\n\n{item.get('body', item.get('snippet', ''))}\n"

        return name, metadata, body


if __name__ == "__main__":
    GmailWatcher.cli_main()
