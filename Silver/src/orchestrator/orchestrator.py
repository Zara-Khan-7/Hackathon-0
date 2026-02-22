"""Orchestrator — watches Needs_Action/ for new .md files, invokes Claude CLI skills.

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
from src.utils.logger import log_action, log_error

load_dotenv()


class Orchestrator:
    """Watches Needs_Action/ and orchestrates the Claude CLI skill pipeline."""

    IGNORE_PREFIXES = ["Plan_"]

    def __init__(self, dry_run: bool = False, poll_interval: int = 10):
        self.dry_run = dry_run
        self.poll_interval = poll_interval
        self.project_root = get_project_root()
        self.claude_cmd = os.getenv("CLAUDE_CMD", "claude")
        self._running = True
        self._processing: set[str] = set()

        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    def _handle_stop(self, signum, frame):
        log_action("Orchestrator", "Shutting down...")
        self._running = False

    def _invoke_claude(self, skill_name: str, context: str) -> str:
        """Invoke a Claude CLI skill with context.

        Returns Claude's response text. In dry-run mode, returns a placeholder.
        """
        if self.dry_run:
            log_action(f"[DRY-RUN] Would invoke skill", f"{skill_name}", "orchestrator")
            return f"[DRY-RUN] Skill '{skill_name}' would be invoked with context."

        prompt = f"Use the {skill_name} skill. Context:\n\n{context}"

        try:
            result = subprocess.run(
                [self.claude_cmd, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root),
            )

            if result.returncode != 0:
                log_error(
                    f"Claude CLI error for {skill_name}",
                    result.stderr[:500],
                    "orchestrator",
                )
                return f"Error: {result.stderr[:500]}"

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            log_error(f"Claude CLI timeout for {skill_name}", "", "orchestrator")
            return "Error: Claude CLI timed out"
        except FileNotFoundError:
            log_error("Claude CLI not found", f"Command: {self.claude_cmd}", "orchestrator")
            return "Error: Claude CLI not found"

    def _classify_task(self, filepath: Path) -> dict:
        """Read and classify a task file."""
        metadata, body = frontmatter.read_file(filepath)

        # Determine task type from filename prefix or metadata
        name = filepath.stem
        task_type = metadata.get("type", "unknown")

        if name.startswith("EMAIL_"):
            task_type = "email"
        elif name.startswith("LINKEDIN_"):
            task_type = "linkedin"
        elif name.startswith("EXECUTE_"):
            task_type = "execute"
        elif name.startswith("SALESPOST_"):
            task_type = "sales_post"
        elif name.startswith("SCHEDULE_"):
            task_type = "schedule"

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

    def _process_task(self, task: dict) -> None:
        """Process a single task through the full pipeline."""
        filepath = task["filepath"]
        filename = task["filename"]
        task_type = task["task_type"]

        log_action("Processing", f"{filename} (type={task_type}, priority={task['priority']})", "orchestrator")

        # Step 1: Create plan (skip for EXECUTE_ tasks which are pre-approved)
        if task_type == "execute":
            self._execute_approved_action(task)
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

        # Step 4: Execute (no approval needed)
        exec_context = (
            f"File: {filename}\n"
            f"Type: {task_type}\n"
            f"Plan:\n{plan_response}\n\n"
            f"Original content:\n{task['body']}"
        )

        if task_type == "sales_post":
            self._invoke_claude("generate_sales_post", exec_context)
        else:
            self._invoke_claude("complete_task", exec_context)

        log_action("Task executed", filename, "orchestrator")

        # Step 5: Cleanup — move to Done/
        safe_move(filepath, "Done")
        log_action("Moved to Done", filename, "orchestrator")

        # Step 6: Update dashboard
        self._invoke_claude("update_dashboard", f"Task completed: {filename}")

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
            "requires_approval": False,  # The approval itself doesn't need approval
        }

        # Copy relevant metadata
        for key in ("from", "subject", "subtype"):
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

        # Move original to Done (it's been processed, approval is separate)
        safe_move(filepath, "Done")

        log_action("Routed to approval", f"{filename} → {approval_path.name}", "orchestrator")

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

        # Cleanup
        safe_move(filepath, "Done")
        log_action("Moved to Done", filename, "orchestrator")

        # Update dashboard
        self._invoke_claude("update_dashboard", f"Executed approved action: {filename}")

    def poll_once(self) -> int:
        """Check Needs_Action/ and process new files."""
        files = list_md_files("Needs_Action", ignore_prefixes=self.IGNORE_PREFIXES)

        # Filter out files currently being processed
        new_files = [f for f in files if f.name not in self._processing]
        if not new_files:
            return 0

        # Classify and sort by priority
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
            except Exception as e:
                log_error(f"Failed to process {task['filename']}", str(e), "orchestrator")
            finally:
                self._processing.discard(task["filename"])

        return processed

    def run(self, once: bool = False) -> None:
        """Main loop — watch Needs_Action/ and process tasks."""
        mode = "dry-run" if self.dry_run else "live"
        log_action("Orchestrator", f"Starting ({mode} mode)", "orchestrator")

        # Process existing files on startup
        self.poll_once()

        if once:
            log_action("Orchestrator", "Single run complete.", "orchestrator")
            return

        while self._running:
            time.sleep(self.poll_interval)
            self.poll_once()

        log_action("Orchestrator", "Stopped.", "orchestrator")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without invoking Claude CLI")
    parser.add_argument("--once", action="store_true", help="Process current files and exit")
    parser.add_argument("--interval", type=int, default=10, help="Poll interval (seconds)")
    args = parser.parse_args()

    orchestrator = Orchestrator(dry_run=args.dry_run, poll_interval=args.interval)
    orchestrator.run(once=args.once)


if __name__ == "__main__":
    main()
