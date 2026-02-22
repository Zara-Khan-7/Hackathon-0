"""Git vault sync — mock implementation for safe operation.

Provides pull/push/sync_cycle operations using mock git operations.
In production, this would call real git subprocess commands.
All operations are logged but use mock implementations to avoid
any dangerous git operations.
"""

import time
from pathlib import Path

from src.utils.file_ops import get_project_root
from src.utils.logger import log_action, log_error


class GitVaultSync:
    """Mock git sync for hybrid cloud/local operation.

    All methods simulate git operations safely without
    actually running git commands.
    """

    def __init__(self, agent_id: str, remote: str = "origin", branch: str = "main"):
        self.agent_id = agent_id
        self.remote = remote
        self.branch = branch
        self.project_root = get_project_root()
        self._last_pull = 0.0
        self._last_push = 0.0
        self._pull_count = 0
        self._push_count = 0

    def pull(self) -> dict:
        """Simulate git pull --rebase.

        In production: git stash && git pull --rebase && git stash pop
        Mock: logs the operation and returns success.
        """
        log_action(
            "[MOCK-GIT] Pull",
            f"agent={self.agent_id} remote={self.remote}/{self.branch}",
            "git_sync",
        )
        self._last_pull = time.time()
        self._pull_count += 1

        return {
            "status": "success",
            "mock": True,
            "agent_id": self.agent_id,
            "operation": "pull",
            "remote": f"{self.remote}/{self.branch}",
            "pull_count": self._pull_count,
        }

    def push(self, message: str | None = None) -> dict:
        """Simulate git add + commit + push.

        In production: git add sync_folders && git commit -m msg && git push
        Mock: logs the operation and returns success.
        """
        if message is None:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{self.agent_id}] Auto-sync {ts}"

        log_action(
            "[MOCK-GIT] Push",
            f"agent={self.agent_id} msg={message[:60]}",
            "git_sync",
        )
        self._last_push = time.time()
        self._push_count += 1

        return {
            "status": "success",
            "mock": True,
            "agent_id": self.agent_id,
            "operation": "push",
            "message": message,
            "push_count": self._push_count,
        }

    def sync_cycle(self) -> dict:
        """Run a full sync cycle: pull then push.

        Used by cloud orchestrator after each poll cycle.
        """
        pull_result = self.pull()
        push_result = self.push()

        return {
            "status": "success",
            "mock": True,
            "pull": pull_result,
            "push": push_result,
        }

    def get_status(self) -> dict:
        """Get sync status information."""
        return {
            "agent_id": self.agent_id,
            "remote": f"{self.remote}/{self.branch}",
            "last_pull": self._last_pull,
            "last_push": self._last_push,
            "pull_count": self._pull_count,
            "push_count": self._push_count,
        }

    def is_repo(self) -> bool:
        """Check if project root is a git repository (mock: always True)."""
        git_dir = self.project_root / ".git"
        return git_dir.exists()
