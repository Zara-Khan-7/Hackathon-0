"""Base class for specialized Diamond-tier agents.

Each agent has a domain, preferred skills, and capability declarations.
The SwarmOrchestrator delegates tasks to the best-matching agent.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """Declares what a specialized agent can do."""
    name: str
    description: str
    task_prefixes: list[str] = field(default_factory=list)
    priority: int = 0  # higher = preferred for this capability


class BaseSpecializedAgent:
    """Abstract base for all specialized agents in the Diamond swarm."""

    AGENT_TYPE: str = "base"
    DISPLAY_NAME: str = "Base Agent"

    def __init__(self, agent_id: str | None = None):
        self.agent_id = agent_id or f"{self.AGENT_TYPE}-agent"
        self.status = AgentStatus.IDLE
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._last_active: float = 0.0
        self._capabilities: list[AgentCapability] = []
        self._register_capabilities()

    def _register_capabilities(self) -> None:
        """Override in subclasses to declare capabilities."""
        pass

    @property
    def capabilities(self) -> list[AgentCapability]:
        return list(self._capabilities)

    @property
    def handled_prefixes(self) -> list[str]:
        """All task prefixes this agent can handle."""
        prefixes = []
        for cap in self._capabilities:
            prefixes.extend(cap.task_prefixes)
        return list(set(prefixes))

    def can_handle(self, task_prefix: str) -> bool:
        """Check if this agent can handle a task with the given prefix."""
        return task_prefix in self.handled_prefixes

    def score_task(self, task: dict) -> int:
        """Score how well this agent can handle a task (higher = better fit).

        Default: sum of capability priorities for matching prefixes.
        Override in subclasses for custom scoring logic.
        """
        filename = task.get("filename", "")
        score = 0
        for cap in self._capabilities:
            for prefix in cap.task_prefixes:
                if filename.startswith(prefix):
                    score += cap.priority + 10
        return score

    def process_task(self, task: dict, dry_run: bool = False) -> dict[str, Any]:
        """Process a task. Returns result dict with status + details.

        Override in subclasses for domain-specific processing.
        """
        self.status = AgentStatus.BUSY
        self._last_active = time.time()
        start = time.time()

        try:
            result = self._execute(task, dry_run)
            self._tasks_completed += 1
            duration_ms = int((time.time() - start) * 1000)
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "agent_type": self.AGENT_TYPE,
                "task": task.get("filename", "unknown"),
                "result": result,
                "duration_ms": duration_ms,
            }
        except Exception as e:
            self._tasks_failed += 1
            return {
                "status": "error",
                "agent_id": self.agent_id,
                "agent_type": self.AGENT_TYPE,
                "task": task.get("filename", "unknown"),
                "error": str(e),
            }
        finally:
            self.status = AgentStatus.IDLE

    def _execute(self, task: dict, dry_run: bool = False) -> str:
        """Core execution logic. Override in subclasses."""
        return f"[{self.AGENT_TYPE}] Processed {task.get('filename', 'unknown')}"

    def get_stats(self) -> dict:
        """Return agent performance stats."""
        return {
            "agent_id": self.agent_id,
            "type": self.AGENT_TYPE,
            "status": self.status.value,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "last_active": self._last_active,
            "capabilities": len(self._capabilities),
        }

    def __repr__(self) -> str:
        return f"{self.DISPLAY_NAME}(id={self.agent_id!r}, status={self.status.value!r})"
