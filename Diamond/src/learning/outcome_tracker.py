"""Outcome Tracker — records task outcomes for the self-improving loop.

Tracks success/failure/partial results per agent, per task type,
enabling the PromptOptimizer to adjust strategies.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Outcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class TaskOutcome:
    """Record of a single task's outcome."""
    task_id: str
    task_type: str
    agent_id: str
    agent_type: str
    outcome: Outcome
    duration_ms: int
    details: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "outcome": self.outcome.value,
            "duration_ms": self.duration_ms,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class OutcomeTracker:
    """Tracks and persists task outcomes for learning."""

    def __init__(self, log_path: str | Path | None = None):
        self._outcomes: list[TaskOutcome] = []
        self._log_path = Path(log_path) if log_path else None

    def record(self, outcome: TaskOutcome) -> None:
        """Record a task outcome."""
        self._outcomes.append(outcome)
        if self._log_path:
            self._append_to_log(outcome)

    def _append_to_log(self, outcome: TaskOutcome) -> None:
        """Append outcome to JSONL log file."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(outcome.to_dict()) + "\n")

    def get_outcomes(self, agent_type: str | None = None,
                     task_type: str | None = None,
                     last_n: int | None = None) -> list[TaskOutcome]:
        """Query outcomes with optional filters."""
        results = self._outcomes
        if agent_type:
            results = [o for o in results if o.agent_type == agent_type]
        if task_type:
            results = [o for o in results if o.task_type == task_type]
        if last_n:
            results = results[-last_n:]
        return results

    def success_rate(self, agent_type: str | None = None,
                     task_type: str | None = None) -> float:
        """Calculate success rate (0.0 to 1.0) with optional filters."""
        outcomes = self.get_outcomes(agent_type=agent_type, task_type=task_type)
        if not outcomes:
            return 0.0
        successes = sum(1 for o in outcomes if o.outcome == Outcome.SUCCESS)
        return successes / len(outcomes)

    def avg_duration(self, agent_type: str | None = None,
                     task_type: str | None = None) -> float:
        """Average task duration in ms."""
        outcomes = self.get_outcomes(agent_type=agent_type, task_type=task_type)
        if not outcomes:
            return 0.0
        return sum(o.duration_ms for o in outcomes) / len(outcomes)

    def failure_patterns(self, min_count: int = 2) -> list[dict]:
        """Identify recurring failure patterns by task type + agent type."""
        failures: dict[str, list[TaskOutcome]] = {}
        for o in self._outcomes:
            if o.outcome in (Outcome.FAILURE, Outcome.TIMEOUT):
                key = f"{o.agent_type}:{o.task_type}"
                failures.setdefault(key, []).append(o)

        patterns = []
        for key, outcomes in failures.items():
            if len(outcomes) >= min_count:
                agent_type, task_type = key.split(":", 1)
                patterns.append({
                    "agent_type": agent_type,
                    "task_type": task_type,
                    "failure_count": len(outcomes),
                    "common_details": self._most_common_detail(outcomes),
                })
        return patterns

    @staticmethod
    def _most_common_detail(outcomes: list[TaskOutcome]) -> str:
        """Find the most common error detail."""
        details: dict[str, int] = {}
        for o in outcomes:
            if o.details:
                details[o.details] = details.get(o.details, 0) + 1
        if not details:
            return ""
        return max(details, key=details.get)

    def get_agent_performance(self) -> list[dict]:
        """Get performance summary per agent type."""
        agent_types: dict[str, list[TaskOutcome]] = {}
        for o in self._outcomes:
            agent_types.setdefault(o.agent_type, []).append(o)

        summaries = []
        for agent_type, outcomes in agent_types.items():
            successes = sum(1 for o in outcomes if o.outcome == Outcome.SUCCESS)
            summaries.append({
                "agent_type": agent_type,
                "total_tasks": len(outcomes),
                "successes": successes,
                "success_rate": successes / len(outcomes) if outcomes else 0,
                "avg_duration_ms": sum(o.duration_ms for o in outcomes) / len(outcomes),
            })
        return summaries

    @property
    def total_outcomes(self) -> int:
        return len(self._outcomes)

    def get_stats(self) -> dict:
        return {
            "total_outcomes": self.total_outcomes,
            "success_rate": self.success_rate(),
            "avg_duration_ms": self.avg_duration(),
            "failure_patterns": len(self.failure_patterns()),
        }
