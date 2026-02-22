"""Sync watcher daemon — pulls from remote on an interval.

Runs on the local machine to keep task folders in sync with cloud.
Mock implementation: simulates periodic git pulls.
"""

import time
import threading

from src.sync.git_sync import GitVaultSync
from src.utils.logger import log_action


class SyncWatcher:
    """Background daemon that pulls from remote git on an interval."""

    def __init__(self, agent_id: str, interval: int = 60,
                 remote: str = "origin", branch: str = "main"):
        self.sync = GitVaultSync(agent_id, remote, branch)
        self.interval = interval
        self._running = False
        self._thread = None

    def start(self) -> None:
        """Start the sync watcher in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        log_action("SyncWatcher", f"Started (interval={self.interval}s)", "sync")

    def stop(self) -> None:
        """Stop the sync watcher."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        log_action("SyncWatcher", "Stopped", "sync")

    def _run_loop(self) -> None:
        """Main loop: pull every interval seconds."""
        while self._running:
            try:
                self.sync.pull()
            except Exception as e:
                log_action("SyncWatcher", f"Pull error: {e}", "sync")
            time.sleep(self.interval)

    def pull_once(self) -> dict:
        """Perform a single pull (for testing/manual use)."""
        return self.sync.pull()

    @property
    def is_running(self) -> bool:
        return self._running
