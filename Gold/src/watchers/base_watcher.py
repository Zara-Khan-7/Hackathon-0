"""Abstract base class for all watchers.

Provides: poll loop, deduplication, --dry-run/--mock CLI flags.
"""

import abc
import argparse
import hashlib
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any

from src.utils.file_ops import get_project_root, create_task_file, get_folder
from src.utils.logger import log_action, log_error


class BaseWatcher(abc.ABC):
    """Base class for source watchers (Gmail, LinkedIn, etc.)."""

    # Subclasses must set these
    NAME: str = "base"
    PREFIX: str = "TASK"
    DEST_FOLDER: str = "Needs_Action"

    def __init__(self, mock: bool = False, dry_run: bool = False, poll_interval: int = 300):
        self.mock = mock
        self.dry_run = dry_run
        self.poll_interval = poll_interval
        self._seen_ids: set[str] = set()
        self._seen_file = get_project_root() / f".{self.NAME}_seen.json"
        self._running = True
        self._load_seen()

        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    def _handle_stop(self, signum, frame):
        log_action(f"{self.NAME} watcher", "Shutting down...")
        self._running = False

    def _load_seen(self) -> None:
        """Load previously seen IDs from disk."""
        if self._seen_file.exists():
            try:
                self._seen_ids = set(json.loads(self._seen_file.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                self._seen_ids = set()

    def _save_seen(self) -> None:
        """Persist seen IDs to disk."""
        try:
            self._seen_file.write_text(
                json.dumps(list(self._seen_ids)), encoding="utf-8"
            )
        except OSError as e:
            log_error("Failed to save seen IDs", str(e), self.NAME)

    def _make_id(self, item: dict[str, Any]) -> str:
        """Generate a dedup ID from an item. Uses 'id' field or content hash."""
        if "id" in item:
            return str(item["id"])
        content = json.dumps(item, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _is_new(self, item: dict[str, Any]) -> bool:
        """Check if an item has already been processed."""
        item_id = self._make_id(item)
        return item_id not in self._seen_ids

    def _mark_seen(self, item: dict[str, Any]) -> None:
        """Mark an item as processed."""
        item_id = self._make_id(item)
        self._seen_ids.add(item_id)

    @abc.abstractmethod
    def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch new items from the source. Subclasses must implement."""
        ...

    @abc.abstractmethod
    def item_to_task(self, item: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Convert a source item to (name, metadata, body) for a task file.

        Returns:
            name: short identifier for the filename
            metadata: YAML frontmatter dict
            body: markdown body content
        """
        ...

    def process_items(self, items: list[dict[str, Any]]) -> int:
        """Process a list of items: dedup, create task files. Returns count created."""
        created = 0
        for item in items:
            if not self._is_new(item):
                continue

            name, metadata, body = self.item_to_task(item)
            metadata["source"] = self.NAME
            metadata["mock"] = self.mock

            if self.dry_run:
                log_action(
                    f"[DRY-RUN] Would create",
                    f"{self.PREFIX}_{name}.md in {self.DEST_FOLDER}/",
                    self.NAME,
                )
            else:
                filepath = create_task_file(self.DEST_FOLDER, self.PREFIX, name, metadata, body)
                log_action("Created task file", str(filepath.name), self.NAME)

            self._mark_seen(item)
            created += 1

        self._save_seen()
        return created

    def poll_once(self) -> int:
        """Run a single poll cycle. Returns number of new items processed."""
        log_action(f"{self.NAME} watcher", "Polling...", self.NAME)
        try:
            items = self.fetch_items()
            log_action(f"{self.NAME} watcher", f"Fetched {len(items)} items", self.NAME)
            return self.process_items(items)
        except Exception as e:
            log_error(f"{self.NAME} poll failed", str(e), self.NAME)
            return 0

    def run(self, once: bool = False) -> None:
        """Main poll loop. If once=True, poll once and exit."""
        mode = "mock" if self.mock else "live"
        log_action(f"{self.NAME} watcher", f"Starting ({mode} mode)", self.NAME)

        while self._running:
            count = self.poll_once()
            if count > 0:
                log_action(f"{self.NAME} watcher", f"Processed {count} new items", self.NAME)

            if once:
                break

            log_action(
                f"{self.NAME} watcher",
                f"Sleeping {self.poll_interval}s...",
                self.NAME,
            )
            time.sleep(self.poll_interval)

        log_action(f"{self.NAME} watcher", "Stopped.", self.NAME)

    @classmethod
    def cli_main(cls, **kwargs) -> None:
        """Entry point for CLI usage with --mock, --dry-run, --once flags."""
        parser = argparse.ArgumentParser(description=f"{cls.NAME} watcher")
        parser.add_argument("--mock", action="store_true", help="Use mock data")
        parser.add_argument("--dry-run", action="store_true", help="Don't create files")
        parser.add_argument("--once", action="store_true", help="Poll once and exit")
        parser.add_argument("--interval", type=int, default=300, help="Poll interval (seconds)")
        args = parser.parse_args()

        watcher = cls(mock=args.mock, dry_run=args.dry_run, poll_interval=args.interval, **kwargs)
        watcher.run(once=args.once)
