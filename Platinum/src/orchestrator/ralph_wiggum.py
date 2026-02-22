"""Ralph Wiggum Loop — state machine + file-movement loop for multi-step autonomous tasks.

Named after Ralph Wiggum's persistent "I'm helping!" attitude, this module
drives complex tasks through multiple Claude CLI invocations until the task
file reaches Done/ (completion) or the iteration limit is hit.

State Machine:
    CREATED → PLANNED → AWAITING_APPROVAL → APPROVED → EXECUTING → COMPLETED
                                                    ↘ FAILED

Each iteration:
1. Read current task state from .ralph_state_{task_id}.json
2. Invoke the appropriate Claude skill based on current state
3. Check if the task file has moved (file-movement detection)
4. Transition state accordingly
5. If Claude output is incomplete, re-invoke with prior context

Usage:
    loop = RalphWiggumLoop(task_filepath, max_iterations=15)
    result = loop.run()
"""

import json
import logging
import os
import subprocess
import time
from enum import Enum
from pathlib import Path

from src.utils.file_ops import get_project_root, get_folder, safe_move
from src.utils.logger import log_action, audit_log
from src.utils import frontmatter

logger = logging.getLogger("ai_employee")


class TaskState(str, Enum):
    CREATED = "created"
    PLANNED = "planned"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


# Skills to invoke per state transition
STATE_SKILLS = {
    TaskState.CREATED: "create_plan",
    TaskState.PLANNED: "complete_task",
    TaskState.APPROVED: "execute_action",
    TaskState.EXECUTING: "complete_task",
}


class RalphWiggumLoop:
    """Drives a complex task through multiple Claude invocations to completion."""

    def __init__(self, task_filepath: str | Path, max_iterations: int = 15,
                 dry_run: bool = False):
        self.task_filepath = Path(task_filepath)
        self.task_id = self.task_filepath.stem
        self.max_iterations = max_iterations
        self.dry_run = dry_run
        self.project_root = get_project_root()
        self.claude_cmd = os.getenv("CLAUDE_CMD", "claude")

        # State file persists across iterations
        self.state_file = self.project_root / f".ralph_state_{self.task_id}.json"

        # Initialize or load state
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load persisted state or initialize fresh."""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)

        return {
            "task_id": self.task_id,
            "task_file": str(self.task_filepath),
            "current_state": TaskState.CREATED.value,
            "iteration": 0,
            "history": [],
            "prior_output": "",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _save_state(self) -> None:
        """Persist state to JSON file."""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, default=str)

    def _transition(self, new_state: TaskState, reason: str = "") -> None:
        """Transition to a new state and log it."""
        old = self.state["current_state"]
        self.state["current_state"] = new_state.value
        self.state["history"].append({
            "from": old,
            "to": new_state.value,
            "reason": reason,
            "iteration": self.state["iteration"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        log_action(
            "Ralph Wiggum",
            f"{self.task_id}: {old} → {new_state.value} ({reason})",
            "ralph_wiggum",
        )
        self._save_state()

    def _invoke_claude(self, skill_name: str, context: str) -> str:
        """Invoke a Claude CLI skill."""
        if self.dry_run:
            log_action(f"[DRY-RUN] Ralph would invoke", skill_name, "ralph_wiggum")
            return f"[DRY-RUN] {skill_name} would process {self.task_id}"

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
                return f"Error: {result.stderr[:500]}"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Error: Claude CLI timed out"
        except FileNotFoundError:
            return "Error: Claude CLI not found"

    def _detect_file_location(self) -> str | None:
        """Check which folder the task file currently lives in.

        Returns the folder name or None if file not found.
        """
        check_folders = ["Needs_Action", "Pending_Approval", "Approved", "Done", "Errors"]
        for folder_name in check_folders:
            folder = get_folder(folder_name)
            # Check for exact filename or variants (with APPROVE_, EXECUTE_ prefix)
            for candidate in folder.glob("*.md"):
                if self.task_id in candidate.stem:
                    return folder_name
        return None

    def _build_context(self) -> str:
        """Build context for Claude invocation based on current state."""
        # Read the current task file content if it still exists
        task_content = ""
        if self.task_filepath.exists():
            meta, body = frontmatter.read_file(self.task_filepath)
            task_content = body

        prior = self.state.get("prior_output", "")

        context = f"Task ID: {self.task_id}\n"
        context += f"Current State: {self.state['current_state']}\n"
        context += f"Iteration: {self.state['iteration']}/{self.max_iterations}\n\n"

        if task_content:
            context += f"## Task Content\n\n{task_content}\n\n"

        if prior:
            context += f"## Prior Output (from last iteration)\n\n{prior}\n\n"

        context += "Complete this step and move the task forward.\n"
        return context

    def run(self) -> dict:
        """Main loop: iterate until COMPLETED, FAILED, or max iterations.

        Returns a summary dict with status, iterations, and history.
        """
        log_action("Ralph Wiggum", f"Starting loop for {self.task_id} (max={self.max_iterations})", "ralph_wiggum")

        while self.state["iteration"] < self.max_iterations:
            current = TaskState(self.state["current_state"])

            # Terminal states — we're done
            if current in (TaskState.COMPLETED, TaskState.FAILED):
                break

            self.state["iteration"] += 1
            self._save_state()

            # Determine which skill to invoke
            skill = STATE_SKILLS.get(current)
            if not skill:
                # For AWAITING_APPROVAL, we just check file location
                location = self._detect_file_location()
                if location == "Approved":
                    self._transition(TaskState.APPROVED, "File found in Approved/")
                    continue
                elif location == "Done":
                    self._transition(TaskState.COMPLETED, "File found in Done/")
                    continue
                elif location == "Errors":
                    self._transition(TaskState.FAILED, "File found in Errors/")
                    continue
                else:
                    # Still waiting for approval — sleep and check again
                    log_action("Ralph Wiggum", f"Waiting for approval ({self.task_id})", "ralph_wiggum")
                    time.sleep(5)
                    continue

            # Build context and invoke Claude
            context = self._build_context()
            output = self._invoke_claude(skill, context)
            self.state["prior_output"] = output[:2000]  # Keep last output for re-injection
            self._save_state()

            # Check where the file ended up after Claude processed it
            location = self._detect_file_location()

            # State transitions based on file location
            if location == "Done":
                self._transition(TaskState.COMPLETED, "File reached Done/")
            elif location == "Pending_Approval":
                self._transition(TaskState.AWAITING_APPROVAL, "File routed to approval")
            elif location == "Approved":
                self._transition(TaskState.APPROVED, "File approved")
            elif location == "Errors":
                self._transition(TaskState.FAILED, "File moved to Errors/")
            else:
                # File still in Needs_Action or skill output suggests more work
                if current == TaskState.CREATED:
                    self._transition(TaskState.PLANNED, "Plan created")
                elif current == TaskState.PLANNED:
                    self._transition(TaskState.EXECUTING, "Execution started")
                elif current == TaskState.APPROVED:
                    self._transition(TaskState.EXECUTING, "Approved action executing")

            # Small delay between iterations
            time.sleep(1)

        # Check if we hit max iterations without completing
        if TaskState(self.state["current_state"]) not in (TaskState.COMPLETED, TaskState.FAILED):
            self._transition(TaskState.FAILED, f"Max iterations ({self.max_iterations}) reached")

            # Move task to Errors/ if it's still in Needs_Action
            if self.task_filepath.exists():
                safe_move(self.task_filepath, "Errors")

        # Cleanup state file on completion
        result = {
            "task_id": self.task_id,
            "status": self.state["current_state"],
            "iterations": self.state["iteration"],
            "history": self.state["history"],
        }

        log_action(
            "Ralph Wiggum",
            f"Loop finished for {self.task_id}: {result['status']} after {result['iterations']} iterations",
            "ralph_wiggum",
        )

        return result
