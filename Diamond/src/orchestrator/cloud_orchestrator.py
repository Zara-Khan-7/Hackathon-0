"""Cloud Orchestrator — extends Gold Orchestrator for cloud-only operation.

Cloud agent restrictions:
- Can only use SAFE + DRAFT MCP tools
- Creates drafts and routes to Pending_Approval/
- Never executes DANGEROUS tools (send_email, post_invoice, etc.)
- Writes heartbeat after each cycle
- Runs git sync after each poll
"""

import time
from pathlib import Path

from src.orchestrator.orchestrator import Orchestrator
from src.config.agent_config import AgentConfig, AgentRole
from src.config.domain_router import should_handle, get_cloud_action, CLOUD_ACTION_SKIP, CLOUD_ACTION_DRAFT
from src.claim.claim_manager import ClaimManager
from src.sync.git_sync import GitVaultSync
from src.health.heartbeat import write_heartbeat
from src.utils.file_ops import list_md_files, safe_move, create_task_file
from src.utils.logger import log_action, audit_log
from src.utils import frontmatter


class CloudOrchestrator(Orchestrator):
    """Cloud-specific orchestrator: draft-only, no dangerous tools."""

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or AgentConfig()
        self.config.role = AgentRole.CLOUD
        self.agent_id = self.config.agent_id
        self.claim_manager = ClaimManager(self.agent_id)
        self.git_sync = GitVaultSync(
            self.agent_id,
            remote=self.config.get("sync", "remote", "origin"),
            branch=self.config.get("sync", "branch", "main"),
        )

    def poll_once(self) -> int:
        """Cloud poll: git pull → filter by domain → claim → draft → git push."""
        # Step 1: Git pull
        if self.config.sync_enabled:
            self.git_sync.pull()

        # Step 2: Scan and filter tasks
        files = list_md_files("Needs_Action", ignore_prefixes=self.IGNORE_PREFIXES)
        new_files = [f for f in files if f.name not in self._processing]

        if not new_files:
            write_heartbeat(self.agent_id)
            if self.config.sync_enabled:
                self.git_sync.push()
            return 0

        # Step 3: Filter by domain routing — skip tasks cloud shouldn't handle
        handleable = []
        for f in new_files:
            if should_handle(f.name, AgentRole.CLOUD):
                handleable.append(f)
            else:
                log_action(
                    "Cloud skip",
                    f"{f.name} (local-only task)",
                    "cloud_orchestrator",
                )

        if not handleable:
            write_heartbeat(self.agent_id)
            if self.config.sync_enabled:
                self.git_sync.push()
            return 0

        # Step 4: Classify, sort, process
        tasks = [self._classify_task(f) for f in handleable]
        tasks = self._sort_by_priority(tasks)

        log_action(
            "Cloud Orchestrator",
            f"Found {len(tasks)} task(s) to process",
            "cloud_orchestrator",
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
                self._process_as_draft(task)
                processed += 1
            except Exception as e:
                log_action(
                    "Cloud error",
                    f"{task['filename']}: {e}",
                    "cloud_orchestrator",
                )
                self.claim_manager.unclaim(claimed_path)
            finally:
                self._processing.discard(task["filename"])

        # Step 5: Heartbeat + git push
        write_heartbeat(self.agent_id)
        if self.config.sync_enabled:
            self.git_sync.push()

        return processed

    def _process_as_draft(self, task: dict) -> None:
        """Process task in draft-only mode: create plan, force approval."""
        filepath = task["filepath"]
        filename = task["filename"]
        cloud_action = get_cloud_action(filename)

        start = time.time()
        audit_log(
            "cloud_task_start",
            actor="cloud_orchestrator",
            agent_id=self.agent_id,
            params={"file": filename, "cloud_action": cloud_action},
            task_name=filename,
        )

        # Create plan
        plan_context = (
            f"File: {filename}\n"
            f"Type: {task['task_type']}\n"
            f"Priority: {task['priority']}\n"
            f"Cloud Action: {cloud_action}\n\n"
            f"Content:\n{task['body']}"
        )

        plan_response = self._invoke_claude("create_plan", plan_context)

        if cloud_action == CLOUD_ACTION_DRAFT:
            # Force route to approval — cloud never executes
            self._route_to_approval(task, plan_response)
            log_action(
                "Cloud draft",
                f"{filename} → Pending_Approval",
                "cloud_orchestrator",
            )
        else:
            # Full action (SCHEDULE_, AUDIT_, ERROR_) — still safe tools only
            exec_context = (
                f"File: {filename}\n"
                f"Type: {task['task_type']}\n"
                f"Plan:\n{plan_response}\n\n"
                f"Original content:\n{task['body']}"
            )
            skill = self._get_skill_for_type(task["task_type"])
            self._invoke_claude(skill, exec_context)
            safe_move(filepath, "Done")
            self._invoke_claude("update_dashboard", f"Cloud completed: {filename}")

        duration = int((time.time() - start) * 1000)
        audit_log(
            "cloud_task_complete",
            actor="cloud_orchestrator",
            agent_id=self.agent_id,
            params={"file": filename, "action": cloud_action},
            result="success",
            duration_ms=duration,
            task_name=filename,
        )
