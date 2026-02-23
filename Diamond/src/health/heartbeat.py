"""Heartbeat writer — signals that an agent is alive.

Writes a JSON heartbeat file to the project root.
"""

import json
import time
from pathlib import Path

from src.utils.file_ops import get_project_root


def write_heartbeat(agent_id: str) -> Path:
    """Write a heartbeat file for the given agent.

    File: .heartbeat_{agent_id}.json
    Contents: agent_id, timestamp, uptime info
    """
    heartbeat_path = get_project_root() / f".heartbeat_{agent_id}.json"
    data = {
        "agent_id": agent_id,
        "timestamp": time.time(),
        "iso_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "alive",
    }
    heartbeat_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return heartbeat_path


def read_heartbeat(agent_id: str) -> dict | None:
    """Read a heartbeat file. Returns None if not found."""
    heartbeat_path = get_project_root() / f".heartbeat_{agent_id}.json"
    if not heartbeat_path.exists():
        return None
    try:
        return json.loads(heartbeat_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def heartbeat_age(agent_id: str) -> float | None:
    """Get the age (in seconds) of an agent's heartbeat. None if not found."""
    hb = read_heartbeat(agent_id)
    if hb is None:
        return None
    return time.time() - hb.get("timestamp", 0)
