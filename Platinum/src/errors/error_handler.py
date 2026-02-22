"""Error detection, retry queue, and graceful degradation for the AI Employee.

Creates ERROR_*.md files in Errors/ for failed tasks, queues them for retry,
and provides notifications for persistent failures.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

from src.utils.file_ops import get_folder, create_task_file, list_md_files
from src.utils.logger import log_action, log_error

logger = logging.getLogger("ai_employee")


class ErrorHandler:
    """Catches exceptions, creates error reports, and manages retry queue."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._retry_counts: dict[str, int] = {}

    def handle_error(
        self,
        error: Exception,
        task_name: str = "unknown",
        task_filepath: str | Path | None = None,
        context: str = "",
    ) -> Path:
        """Record an error and create an ERROR_*.md in Errors/.

        Returns the path to the error report file.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_type = type(error).__name__
        error_msg = str(error)
        tb = traceback.format_exception(type(error), error, error.__traceback__)

        # Track retry count
        retry_key = task_name
        current = self._retry_counts.get(retry_key, 0) + 1
        self._retry_counts[retry_key] = current
        can_retry = current < self.max_retries

        metadata = {
            "type": "error",
            "error_type": error_type,
            "task_name": task_name,
            "retry_count": current,
            "max_retries": self.max_retries,
            "can_retry": can_retry,
            "status": "pending_retry" if can_retry else "failed",
            "created": timestamp,
            "priority": "high",
        }
        if task_filepath:
            metadata["original_file"] = str(task_filepath)

        body = f"# Error Report: {task_name}\n\n"
        body += f"**Error:** {error_type}: {error_msg}\n"
        body += f"**Time:** {timestamp}\n"
        body += f"**Retry:** {current}/{self.max_retries}\n"
        body += f"**Can Retry:** {'Yes' if can_retry else 'No — escalate to human'}\n\n"

        if context:
            body += f"## Context\n\n{context}\n\n"

        body += "## Traceback\n\n```\n"
        body += "".join(tb)
        body += "```\n"

        safe_task = task_name.replace(" ", "_")[:60]
        error_path = create_task_file("Errors", "ERROR", safe_task, metadata, body)

        log_error(
            f"Error captured for {task_name}",
            f"{error_type}: {error_msg} (retry {current}/{self.max_retries})",
            "error_handler",
        )

        return error_path

    def can_retry(self, task_name: str) -> bool:
        """Check if a task can still be retried."""
        return self._retry_counts.get(task_name, 0) < self.max_retries

    def reset_retries(self, task_name: str) -> None:
        """Reset retry count (e.g. after a successful run)."""
        self._retry_counts.pop(task_name, None)

    def get_pending_retries(self) -> list[Path]:
        """List error files that are still eligible for retry."""
        from src.utils import frontmatter

        error_files = list_md_files("Errors")
        retryable = []
        for f in error_files:
            meta, _ = frontmatter.read_file(f)
            if meta.get("can_retry") and meta.get("status") == "pending_retry":
                retryable.append(f)
        return retryable

    def get_failed_tasks(self) -> list[Path]:
        """List error files that have exhausted retries."""
        from src.utils import frontmatter

        error_files = list_md_files("Errors")
        failed = []
        for f in error_files:
            meta, _ = frontmatter.read_file(f)
            if meta.get("status") == "failed":
                failed.append(f)
        return failed


def graceful_call(func, *args, error_handler: ErrorHandler | None = None,
                  task_name: str = "unknown", context: str = "", **kwargs):
    """Call a function with graceful error handling.

    If the function raises, captures the error and returns None.
    Useful for MCP calls where failure shouldn't crash the pipeline.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.handle_error(e, task_name=task_name, context=context)
        else:
            log_error(f"Unhandled error in {task_name}", str(e), "error_handler")
        return None
