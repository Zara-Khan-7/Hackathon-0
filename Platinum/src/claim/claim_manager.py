"""Claim-by-move task ownership.

Provides atomic claim/unclaim for task files using os.rename().
Each agent claims tasks by moving them to In_Progress/{agent_id}/.
"""

import os
import time
from pathlib import Path

from src.utils.file_ops import get_project_root, get_folder
from src.utils.logger import log_action, log_error


class ClaimManager:
    """Manages task ownership via file system moves."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.project_root = get_project_root()

    def _get_agent_folder(self) -> Path:
        """Get or create the In_Progress/{agent_id}/ folder."""
        folder = get_folder("In_Progress") / self.agent_id
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def claim(self, filepath: str | Path) -> Path | None:
        """Claim a task by moving it to In_Progress/{agent_id}/.

        Uses os.rename() for atomicity on same filesystem.
        Returns the new file path, or None if claim failed.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            log_error("Claim failed", f"File not found: {filepath.name}", "claim")
            return None

        dest_folder = self._get_agent_folder()
        dest_path = dest_folder / filepath.name

        if dest_path.exists():
            log_error("Claim failed", f"Already claimed: {filepath.name}", "claim")
            return None

        try:
            os.rename(str(filepath), str(dest_path))
            log_action("Claimed", f"{filepath.name} → {self.agent_id}", "claim")
            return dest_path
        except OSError as e:
            log_error("Claim failed", f"{filepath.name}: {e}", "claim")
            return None

    def unclaim(self, filepath: str | Path) -> Path | None:
        """Release a claimed task back to Needs_Action/.

        Used when processing fails and the task should be retried.
        Returns the new file path, or None if unclaim failed.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            log_error("Unclaim failed", f"File not found: {filepath.name}", "claim")
            return None

        dest_folder = get_folder("Needs_Action")
        dest_path = dest_folder / filepath.name

        try:
            os.rename(str(filepath), str(dest_path))
            log_action("Unclaimed", f"{filepath.name} → Needs_Action", "claim")
            return dest_path
        except OSError as e:
            log_error("Unclaim failed", f"{filepath.name}: {e}", "claim")
            return None

    def list_claimed(self) -> list[Path]:
        """List all files currently claimed by this agent."""
        folder = self._get_agent_folder()
        return sorted(folder.glob("*.md"))

    def cleanup_stale(self, max_age_seconds: int = 3600) -> list[Path]:
        """Move files stuck in In_Progress for too long back to Needs_Action/.

        Checks ALL agent folders, not just this agent's.
        Returns list of files that were moved back.
        """
        in_progress = get_folder("In_Progress")
        moved_back = []
        now = time.time()

        for agent_folder in in_progress.iterdir():
            if not agent_folder.is_dir() or agent_folder.name.startswith("."):
                continue

            for md_file in agent_folder.glob("*.md"):
                age = now - md_file.stat().st_mtime
                if age > max_age_seconds:
                    result = self.unclaim(md_file)
                    if result:
                        moved_back.append(result)
                        log_action(
                            "Stale cleanup",
                            f"{md_file.name} was stuck for {int(age)}s",
                            "claim",
                        )

        return moved_back

    def is_claimed(self, filename: str) -> bool:
        """Check if a file is claimed by any agent."""
        in_progress = get_folder("In_Progress")
        for agent_folder in in_progress.iterdir():
            if agent_folder.is_dir() and (agent_folder / filename).exists():
                return True
        return False

    def get_claim_owner(self, filename: str) -> str | None:
        """Get the agent_id that claimed a file, or None."""
        in_progress = get_folder("In_Progress")
        for agent_folder in in_progress.iterdir():
            if agent_folder.is_dir() and (agent_folder / filename).exists():
                return agent_folder.name
        return None
