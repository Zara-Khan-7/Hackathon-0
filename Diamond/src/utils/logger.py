"""Structured logging to Logs/ folder and console.

Includes JSON-lines audit logger for machine-parseable action trails.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from src.utils.file_ops import get_folder


def _get_log_file(task_name: str = "system") -> Path:
    """Get the log file path for today + task."""
    logs_dir = get_folder("Logs")
    date_str = datetime.now().strftime("%Y-%m-%d")
    return logs_dir / f"{date_str}_{task_name}.md"


def _setup_console_logger() -> logging.Logger:
    """Set up a console logger."""
    logger = logging.getLogger("ai_employee")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


_console = _setup_console_logger()


def log_action(action: str, details: str = "", task_name: str = "system") -> None:
    """Log an action to both console and Logs/ folder."""
    _console.info(f"{action}: {details}" if details else action)

    log_file = _get_log_file(task_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"- **[{timestamp}]** {action}"
    if details:
        entry += f": {details}"
    entry += "\n"

    # Append to log file, creating header if new
    if not log_file.exists():
        header = f"# Log: {task_name}\n\n**Date:** {timestamp[:10]}\n\n## Actions\n\n"
        log_file.write_text(header + entry, encoding="utf-8")
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)


def log_error(error: str, details: str = "", task_name: str = "system") -> None:
    """Log an error to both console and Logs/ folder."""
    _console.error(f"{error}: {details}" if details else error)

    log_file = _get_log_file(task_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"- **[{timestamp}] ERROR** {error}"
    if details:
        entry += f": {details}"
    entry += "\n"

    if not log_file.exists():
        header = f"# Log: {task_name}\n\n**Date:** {timestamp[:10]}\n\n## Actions\n\n"
        log_file.write_text(header + entry, encoding="utf-8")
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)


# ---------------------------------------------------------------------------
# JSON-lines audit logger
# ---------------------------------------------------------------------------

def _get_audit_file() -> Path:
    """Get today's JSON-lines audit log path."""
    logs_dir = get_folder("Logs")
    date_str = datetime.now().strftime("%Y-%m-%d")
    return logs_dir / f"{date_str}_actions.jsonl"


def audit_log(
    action_type: str,
    actor: str = "orchestrator",
    params: dict | None = None,
    approval_status: str | None = None,
    result: str = "success",
    duration_ms: int | None = None,
    task_name: str | None = None,
    agent_id: str | None = None,
) -> None:
    """Append a machine-parseable JSON-lines audit record.

    Fields: timestamp, action_type, actor, agent_id, params, approval_status,
            result, duration_ms, task_name
    """
    record = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "actor": actor,
    }
    if agent_id:
        record["agent_id"] = agent_id
    if params:
        record["params"] = params
    if approval_status:
        record["approval_status"] = approval_status
    if result:
        record["result"] = result
    if duration_ms is not None:
        record["duration_ms"] = duration_ms
    if task_name:
        record["task_name"] = task_name

    audit_file = _get_audit_file()
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
