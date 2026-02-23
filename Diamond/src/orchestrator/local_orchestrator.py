"""Local Orchestrator — extends Gold Orchestrator for local-only operation.

Local agent capabilities:
- Has access to ALL MCP tools (including DANGEROUS)
- Handles WhatsApp and Payment tasks
- Processes EXECUTE_ tasks (pre-approved actions)
- Runs approval watcher for HITL review
- Has full access to secrets and credentials
"""

import time
from pathlib import Path

from src.orchestrator.orchestrator import Orchestrator
from src.config.agent_config import AgentConfig, AgentRole
from src.config.domain_router import should_handle
from src.claim.claim_manager import ClaimManager
from src.sync.git_sync import GitVaultSync
from src.health.heartbeat import write_heartbeat
from src.utils.file_ops import list_md_files, safe_move
from src.utils.logger import log_action, audit_log


class LocalOrchestrator(Orchestrator):
    """Local-specific orchestrator: full tool access, handles all tasks."""

    # Extended skill routing with WhatsApp and Payment
    EXTENDED_SKILL_ROUTING = {
        "whatsapp": "whatsapp_reply",
        "payment": "process_payment",
    }

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or AgentConfig()
        self.config.role = AgentRole.LOCAL
        self.agent_id = self.config.agent_id
        self.claim_manager = ClaimManager(self.agent_id)
        self.git_sync = GitVaultSync(
            self.agent_id,
            remote=self.config.get("sync", "remote", "origin"),
            branch=self.config.get("sync", "branch", "main"),
        )

    def _get_skill_for_type(self, task_type: str) -> str:
        """Extended skill routing with WhatsApp and Payment types."""
        if task_type in self.EXTENDED_SKILL_ROUTING:
            return self.EXTENDED_SKILL_ROUTING[task_type]
        return super()._get_skill_for_type(task_type)

    def _classify_task(self, filepath: Path) -> dict:
        """Extended classification with WhatsApp and Payment prefixes."""
        task = super()._classify_task(filepath)

        # Add Platinum-specific prefix mappings
        name = filepath.stem
        if name.startswith("WHATSAPP_"):
            task["task_type"] = "whatsapp"
        elif name.startswith("PAYMENT_"):
            task["task_type"] = "payment"

        return task

    def poll_once(self) -> int:
        """Local poll: git pull → process ALL tasks → git push."""
        # Step 1: Git pull
        if self.config.sync_enabled:
            self.git_sync.pull()

        # Step 2: Cleanup stale claims
        self.claim_manager.cleanup_stale(max_age_seconds=3600)

        # Step 3: Scan tasks
        files = list_md_files("Needs_Action", ignore_prefixes=self.IGNORE_PREFIXES)
        new_files = [f for f in files if f.name not in self._processing]

        if not new_files:
            write_heartbeat(self.agent_id)
            if self.config.sync_enabled:
                self.git_sync.push()
            return 0

        # Step 4: Classify, sort, process (local handles ALL tasks)
        tasks = [self._classify_task(f) for f in new_files]
        tasks = self._sort_by_priority(tasks)

        log_action(
            "Local Orchestrator",
            f"Found {len(tasks)} task(s) to process",
            "local_orchestrator",
        )

        processed = 0
        for task in tasks:
            if not self._running:
                break

            # Claim the task
            claimed_path = self.claim_manager.claim(task["filepath"])
            if claimed_path is None:
                continue

            task["filepath"] = claimed_path
            self._processing.add(task["filename"])

            try:
                self._process_task(task)
                processed += 1
                self.error_handler.reset_retries(task["filename"])
            except Exception as e:
                log_action(
                    "Local error",
                    f"{task['filename']}: {e}",
                    "local_orchestrator",
                )
                self.claim_manager.unclaim(claimed_path)
                self.error_handler.handle_error(
                    e,
                    task_name=task["filename"],
                    task_filepath=task["filepath"],
                    context=f"Local processing failed for type={task['task_type']}",
                )
            finally:
                self._processing.discard(task["filename"])

        # Step 5: Heartbeat + git push
        write_heartbeat(self.agent_id)
        if self.config.sync_enabled:
            self.git_sync.push()

        return processed
