"""Orchestrator — watches Needs_Action/ for new .md files, invokes Claude CLI skills.

Gold Tier enhancements:
- New prefixes: ODOO_, FACEBOOK_, INSTAGRAM_, TWITTER_, SOCIAL_, AUDIT_, ERROR_
- Error recovery with retry decorator + ErrorHandler
- Audit logging (JSON-lines) for all actions
- Ralph Wiggum loop integration for complex multi-step tasks

Pipeline per file:
1. Scan & classify the task (read frontmatter)
2. Create plan (invoke create_plan skill)
3. Check if approval needed → route to Pending_Approval/
4. If no approval needed → execute (invoke complete_task skill)
5. Cleanup: move to Done/
6. Update Dashboard

Supports --dry-run to log actions without calling Claude CLI.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from src.utils import frontmatter
from src.utils.file_ops import (
    get_folder,
    get_project_root,
    list_md_files,
    safe_move,
    create_task_file,
)
from src.utils.logger import log_action, log_error, audit_log
from src.utils.retry import with_retry, RetryExhausted
from src.errors.error_handler import ErrorHandler, graceful_call

load_dotenv()


class Orchestrator:
    """Watches Needs_Action/ and orchestrates the Claude CLI skill pipeline."""

    IGNORE_PREFIXES = ["Plan_"]

    # Prefix → skill routing map
    SKILL_ROUTING = {
        "execute": "execute_action",
        "sales_post": "generate_sales_post",
        "odoo_sync": "sync_odoo_transactions",
        "odoo_invoice": "create_invoice_draft",
        "odoo_post": "post_approved_invoice",
        "social_post": "generate_social_post",
        "social_approved": "post_approved_social",
        "social_summary": "summarize_social_activity",
        "audit": "weekly_audit",
        "error": "handle_error",
    }

    # Prefixes that trigger Ralph Wiggum loop for multi-step processing
    COMPLEX_PREFIXES = ["ODOO_", "AUDIT_"]

    def __init__(self, dry_run: bool = False, poll_interval: int = 10,
                 ralph_enabled: bool = True):
        self.dry_run = dry_run
        self.poll_interval = poll_interval
        self.ralph_enabled = ralph_enabled
        self.project_root = get_project_root()
        self.claude_cmd = os.getenv("CLAUDE_CMD", "claude")
        self._running = True
        self._processing: set[str] = set()
        self.error_handler = ErrorHandler(max_retries=3)

        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    def _handle_stop(self, signum, frame):
        log_action("Orchestrator", "Shutting down...")
        self._running = False

    @staticmethod
    def _invoke_claude_raw(claude_cmd: str, project_root: str, skill_name: str, context: str) -> str:
        """Raw Claude CLI invocation (static for retry decorator compatibility)."""
        prompt = f"Use the {skill_name} skill. Context:\n\n{context}"
        result = subprocess.run(
            [claude_cmd, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=project_root,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr[:500]}")
        return result.stdout.strip()

    def _invoke_claude(self, skill_name: str, context: str) -> str:
        """Invoke a Claude CLI skill with context, with retry and audit logging.

        Returns Claude's response text. In dry-run mode, returns a placeholder.
        """
        start = time.time()

        if self.dry_run:
            log_action(f"[DRY-RUN] Would invoke skill", f"{skill_name}", "orchestrator")
            audit_log("skill_invoke", actor="orchestrator",
                      params={"skill": skill_name, "dry_run": True},
                      result="dry_run")
            return f"[DRY-RUN] Skill '{skill_name}' would be invoked with context."

        try:
            # Use retry wrapper for resilience
            @with_retry(max_attempts=2, backoff_factor=2)
            def _call():
                return self._invoke_claude_raw(
                    self.claude_cmd, str(self.project_root), skill_name, context
                )

            response = _call()
            duration = int((time.time() - start) * 1000)
            audit_log("skill_invoke", actor="orchestrator",
                      params={"skill": skill_name},
                      result="success", duration_ms=duration)
            return response

        except RetryExhausted as e:
            duration = int((time.time() - start) * 1000)
            audit_log("skill_invoke", actor="orchestrator",
                      params={"skill": skill_name},
                      result="failed", duration_ms=duration)
            self.error_handler.handle_error(
                e, task_name=f"skill:{skill_name}",
                context=f"Failed to invoke {skill_name} after retries"
            )
            return f"Error: {e}"

        except FileNotFoundError:
            log_error("Claude CLI not found", f"Command: {self.claude_cmd}", "orchestrator")
            audit_log("skill_invoke", actor="orchestrator",
                      params={"skill": skill_name},
                      result="cli_not_found")
            return "Error: Claude CLI not found"

    def _classify_task(self, filepath: Path) -> dict:
        """Read and classify a task file."""
        metadata, body = frontmatter.read_file(filepath)

        # Determine task type from filename prefix or metadata
        name = filepath.stem
        task_type = metadata.get("type", "unknown")

        prefix_map = {
            "EMAIL_": "email",
            "LINKEDIN_": "linkedin",
            "EXECUTE_": "execute",
            "SALESPOST_": "sales_post",
            "SCHEDULE_": "schedule",
            "ODOO_": "odoo",
            "FACEBOOK_": "facebook",
            "INSTAGRAM_": "instagram",
            "TWITTER_": "twitter",
            "SOCIAL_": "social",
            "AUDIT_": "audit",
            "ERROR_": "error",
        }

        for prefix, ttype in prefix_map.items():
            if name.startswith(prefix):
                task_type = ttype
                break

        return {
            "filepath": filepath,
            "filename": filepath.name,
            "task_type": task_type,
            "priority": metadata.get("priority", "medium"),
            "requires_approval": metadata.get("requires_approval", False),
            "metadata": metadata,
            "body": body,
        }

    def _sort_by_priority(self, tasks: list[dict]) -> list[dict]:
        """Sort tasks by priority: high > medium > low."""
        order = {"high": 0, "medium": 1, "low": 2}
        return sorted(tasks, key=lambda t: order.get(t["priority"], 1))

    def _is_complex_task(self, task: dict) -> bool:
        """Check if a task should use the Ralph Wiggum loop."""
        if not self.ralph_enabled:
            return False
        return any(task["filename"].startswith(p) for p in self.COMPLEX_PREFIXES)

    def _process_task(self, task: dict) -> None:
        """Process a single task through the full pipeline."""
        filepath = task["filepath"]
        filename = task["filename"]
        task_type = task["task_type"]
        start = time.time()

        log_action("Processing", f"{filename} (type={task_type}, priority={task['priority']})", "orchestrator")
        audit_log("task_start", actor="orchestrator",
                  params={"file": filename, "type": task_type, "priority": task["priority"]},
                  task_name=filename)

        # Check if this is a Ralph Wiggum complex task
        if self._is_complex_task(task):
            self._process_with_ralph(task)
            return

        # Step 1: Handle EXECUTE_ tasks (pre-approved)
        if task_type == "execute":
            self._execute_approved_action(task)
            return

        # Step 1b: Handle ERROR_ tasks
        if task_type == "error":
            self._invoke_claude("handle_error", f"File: {filename}\n\nContent:\n{task['body']}")
            safe_move(filepath, "Done")
            return

        # Step 2: Invoke create_plan skill
        plan_context = (
            f"File: {filename}\n"
            f"Type: {task_type}\n"
            f"Priority: {task['priority']}\n"
            f"Requires Approval: {task['requires_approval']}\n\n"
            f"Content:\n{task['body']}"
        )

        plan_response = self._invoke_claude("create_plan", plan_context)
        log_action("Plan created", filename, "orchestrator")

        # Step 3: Check approval requirement
        if task["requires_approval"]:
            self._route_to_approval(task, plan_response)
            return

        # Step 4: Execute (no approval needed) — route to correct skill
        exec_context = (
            f"File: {filename}\n"
            f"Type: {task_type}\n"
            f"Plan:\n{plan_response}\n\n"
            f"Original content:\n{task['body']}"
        )

        skill = self._get_skill_for_type(task_type)
        self._invoke_claude(skill, exec_context)
        log_action("Task executed", filename, "orchestrator")

        # Step 5: Cleanup — move to Done/
        safe_move(filepath, "Done")
        log_action("Moved to Done", filename, "orchestrator")

        # Step 6: Update dashboard
        self._invoke_claude("update_dashboard", f"Task completed: {filename}")

        duration = int((time.time() - start) * 1000)
        audit_log("task_complete", actor="orchestrator",
                  params={"file": filename, "type": task_type},
                  result="success", duration_ms=duration, task_name=filename)

    def _get_skill_for_type(self, task_type: str) -> str:
        """Map task type to the appropriate skill name."""
        type_to_skill = {
            "sales_post": "generate_sales_post",
            "odoo": "sync_odoo_transactions",
            "facebook": "generate_social_post",
            "instagram": "generate_social_post",
            "twitter": "generate_social_post",
            "social": "summarize_social_activity",
            "audit": "weekly_audit",
            "error": "handle_error",
        }
        return type_to_skill.get(task_type, "complete_task")

    def _process_with_ralph(self, task: dict) -> None:
        """Process a complex task using the Ralph Wiggum loop."""
        from src.orchestrator.ralph_wiggum import RalphWiggumLoop

        filepath = task["filepath"]
        log_action("Ralph Wiggum", f"Starting loop for {task['filename']}", "orchestrator")
        audit_log("ralph_start", actor="ralph_wiggum",
                  params={"file": task["filename"]}, task_name=task["filename"])

        loop = RalphWiggumLoop(filepath, max_iterations=15, dry_run=self.dry_run)
        result = loop.run()

        audit_log("ralph_complete", actor="ralph_wiggum",
                  params={"file": task["filename"], "iterations": result.get("iterations", 0)},
                  result=result.get("status", "unknown"), task_name=task["filename"])

    def _route_to_approval(self, task: dict, plan_response: str) -> None:
        """Route a task to Pending_Approval/ for HITL review."""
        filepath = task["filepath"]
        filename = task["filename"]

        approval_metadata = {
            "type": "approval",
            "original_task": filename,
            "task_type": task["task_type"],
            "priority": task["priority"],
            "status": "pending_approval",
            "requires_approval": False,
        }

        for key in ("from", "subject", "subtype", "platform"):
            if key in task["metadata"]:
                approval_metadata[key] = task["metadata"][key]

        approval_body = f"# Approval Request: {filename}\n\n"
        approval_body += f"**Original Task:** {filename}\n"
        approval_body += f"**Type:** {task['task_type']}\n"
        approval_body += f"**Priority:** {task['priority']}\n\n"
        approval_body += f"## Plan\n\n{plan_response}\n\n"
        approval_body += f"## Original Content\n\n{task['body']}\n"

        task_name = filepath.stem
        approval_path = create_task_file(
            "Pending_Approval", "APPROVE", task_name, approval_metadata, approval_body
        )

        safe_move(filepath, "Done")

        log_action("Routed to approval", f"{filename} → {approval_path.name}", "orchestrator")
        audit_log("route_approval", actor="orchestrator",
                  params={"file": filename, "approval_file": approval_path.name},
                  approval_status="pending", task_name=filename)

    def _execute_approved_action(self, task: dict) -> None:
        """Execute a pre-approved action (EXECUTE_* files)."""
        filepath = task["filepath"]
        filename = task["filename"]

        exec_context = (
            f"File: {filename}\n"
            f"This action has been APPROVED by the user.\n"
            f"Type: {task['task_type']}\n\n"
            f"Content:\n{task['body']}"
        )

        self._invoke_claude("execute_action", exec_context)
        log_action("Executed approved action", filename, "orchestrator")

        safe_move(filepath, "Done")
        log_action("Moved to Done", filename, "orchestrator")

        self._invoke_claude("update_dashboard", f"Executed approved action: {filename}")
        audit_log("execute_approved", actor="orchestrator",
                  params={"file": filename}, approval_status="approved",
                  result="success", task_name=filename)

    def poll_once(self) -> int:
        """Check Needs_Action/ and process new files."""
        files = list_md_files("Needs_Action", ignore_prefixes=self.IGNORE_PREFIXES)

        new_files = [f for f in files if f.name not in self._processing]
        if not new_files:
            return 0

        tasks = [self._classify_task(f) for f in new_files]
        tasks = self._sort_by_priority(tasks)

        log_action("Orchestrator", f"Found {len(tasks)} task(s) to process", "orchestrator")

        processed = 0
        for task in tasks:
            if not self._running:
                break

            self._processing.add(task["filename"])
            try:
                self._process_task(task)
                processed += 1
                self.error_handler.reset_retries(task["filename"])
            except Exception as e:
                log_error(f"Failed to process {task['filename']}", str(e), "orchestrator")
                self.error_handler.handle_error(
                    e, task_name=task["filename"],
                    task_filepath=task["filepath"],
                    context=f"Processing failed for task type={task['task_type']}"
                )
            finally:
                self._processing.discard(task["filename"])

        return processed

    def run(self, once: bool = False) -> None:
        """Main loop — watch Needs_Action/ and process tasks."""
        mode = "dry-run" if self.dry_run else "live"
        log_action("Orchestrator", f"Starting ({mode} mode, ralph={'on' if self.ralph_enabled else 'off'})", "orchestrator")
        audit_log("orchestrator_start", actor="orchestrator",
                  params={"mode": mode, "ralph_enabled": self.ralph_enabled})

        self.poll_once()

        if once:
            log_action("Orchestrator", "Single run complete.", "orchestrator")
            return

        while self._running:
            time.sleep(self.poll_interval)
            self.poll_once()

        log_action("Orchestrator", "Stopped.", "orchestrator")
        audit_log("orchestrator_stop", actor="orchestrator")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Orchestrator — Gold Tier")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without invoking Claude CLI")
    parser.add_argument("--once", action="store_true", help="Process current files and exit")
    parser.add_argument("--interval", type=int, default=10, help="Poll interval (seconds)")
    parser.add_argument("--no-ralph", action="store_true", help="Disable Ralph Wiggum loop")
    args = parser.parse_args()

    orchestrator = Orchestrator(
        dry_run=args.dry_run,
        poll_interval=args.interval,
        ralph_enabled=not args.no_ralph,
    )
    orchestrator.run(once=args.once)


if __name__ == "__main__":
    main()
