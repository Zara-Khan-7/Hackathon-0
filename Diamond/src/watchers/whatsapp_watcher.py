"""WhatsApp Watcher — LOCAL-ONLY, creates WHATSAPP_*.md from new messages.

Polls mock WhatsApp chats and creates task files for unread messages.
"""

import json
import os
from pathlib import Path

from src.mcp_whatsapp.mock_whatsapp import get_chats
from src.utils.file_ops import get_project_root, get_folder, create_task_file, file_exists
from src.utils.logger import log_action


SEEN_FILE = ".whatsapp_seen.json"


class WhatsAppWatcher:
    """Watches WhatsApp chats for new messages (LOCAL-ONLY)."""

    def __init__(self, max_per_poll: int = 10):
        self.max_per_poll = max_per_poll
        self.project_root = get_project_root()
        self._seen = self._load_seen()

    def _seen_path(self) -> Path:
        return self.project_root / SEEN_FILE

    def _load_seen(self) -> set:
        path = self._seen_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return set(data)
            except (json.JSONDecodeError, OSError):
                pass
        return set()

    def _save_seen(self) -> None:
        self._seen_path().write_text(
            json.dumps(list(self._seen)), encoding="utf-8"
        )

    def poll_once(self) -> int:
        """Check for unread WhatsApp messages and create task files."""
        chats = get_chats()
        created = 0

        for chat in chats:
            if created >= self.max_per_poll:
                break

            chat_id = chat["chat_id"]
            if chat.get("unread", 0) == 0:
                continue
            if chat_id in self._seen:
                continue

            # Create WHATSAPP_ task
            metadata = {
                "type": "whatsapp",
                "priority": "medium",
                "requires_approval": True,
                "from": chat["name"],
                "phone": chat["phone"],
                "chat_id": chat_id,
            }

            body = f"# New WhatsApp Message\n\n"
            body += f"**From:** {chat['name']}\n"
            body += f"**Phone:** {chat['phone']}\n"
            body += f"**Time:** {chat['last_time']}\n\n"
            body += f"## Message\n\n{chat['last_message']}\n"

            task_path = create_task_file(
                "Needs_Action", "WHATSAPP", chat_id, metadata, body
            )

            self._seen.add(chat_id)
            created += 1
            log_action(
                "WhatsApp watcher",
                f"Created {task_path.name}",
                "whatsapp_watcher",
            )

        self._save_seen()
        return created
