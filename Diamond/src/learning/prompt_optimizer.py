"""Prompt Optimizer — adjusts agent strategies based on outcome feedback.

Analyzes patterns in the OutcomeTracker and generates optimization
suggestions for the SwarmOrchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.learning.outcome_tracker import OutcomeTracker, Outcome


@dataclass
class Optimization:
    """A single optimization recommendation."""
    agent_type: str
    task_type: str
    recommendation: str
    confidence: float  # 0.0 to 1.0
    based_on_samples: int


class PromptOptimizer:
    """Analyzes outcomes and generates optimization suggestions.

    In production, this could use ML models. The mock version uses
    rule-based heuristics for demonstrations.
    """

    def __init__(self, tracker: OutcomeTracker, min_sample_size: int = 10):
        self._tracker = tracker
        self._min_sample_size = min_sample_size
        self._applied_optimizations: list[Optimization] = []

    def analyze(self) -> list[Optimization]:
        """Run optimization analysis and return recommendations."""
        optimizations = []

        # Check for poor-performing agent-task combinations
        optimizations.extend(self._check_agent_reassignment())

        # Check for high failure rates by task type
        optimizations.extend(self._check_failure_patterns())

        # Check for slow agents
        optimizations.extend(self._check_slow_agents())

        return optimizations

    def _check_agent_reassignment(self) -> list[Optimization]:
        """Recommend reassigning tasks if an agent struggles with a type."""
        results = []
        performance = self._tracker.get_agent_performance()

        for perf in performance:
            if perf["total_tasks"] < self._min_sample_size:
                continue

            if perf["success_rate"] < 0.7:
                results.append(Optimization(
                    agent_type=perf["agent_type"],
                    task_type="all",
                    recommendation=(
                        f"Agent '{perf['agent_type']}' has low success rate "
                        f"({perf['success_rate']:.0%}). Consider redistributing "
                        f"tasks or adjusting agent prompts."
                    ),
                    confidence=min(0.9, perf["total_tasks"] / 50),
                    based_on_samples=perf["total_tasks"],
                ))

        return results

    def _check_failure_patterns(self) -> list[Optimization]:
        """Identify recurring failure patterns."""
        results = []
        patterns = self._tracker.failure_patterns(min_count=3)

        for pattern in patterns:
            results.append(Optimization(
                agent_type=pattern["agent_type"],
                task_type=pattern["task_type"],
                recommendation=(
                    f"Recurring failure: {pattern['agent_type']} fails on "
                    f"'{pattern['task_type']}' tasks ({pattern['failure_count']} times). "
                    f"Common error: {pattern['common_details'] or 'unknown'}. "
                    f"Consider adding error handling or different approach."
                ),
                confidence=min(0.95, pattern["failure_count"] / 10),
                based_on_samples=pattern["failure_count"],
            ))

        return results

    def _check_slow_agents(self) -> list[Optimization]:
        """Check for agents that are consistently slow."""
        results = []
        performance = self._tracker.get_agent_performance()

        for perf in performance:
            if perf["total_tasks"] < self._min_sample_size:
                continue

            avg_ms = perf["avg_duration_ms"]
            if avg_ms > 30000:  # > 30 seconds average
                results.append(Optimization(
                    agent_type=perf["agent_type"],
                    task_type="all",
                    recommendation=(
                        f"Agent '{perf['agent_type']}' is slow "
                        f"(avg {avg_ms:.0f}ms per task). Consider optimizing "
                        f"prompts or breaking tasks into smaller steps."
                    ),
                    confidence=0.7,
                    based_on_samples=perf["total_tasks"],
                ))

        return results

    def apply(self, optimization: Optimization) -> None:
        """Mark an optimization as applied (for tracking)."""
        self._applied_optimizations.append(optimization)

    def get_stats(self) -> dict:
        return {
            "total_outcomes": self._tracker.total_outcomes,
            "min_sample_size": self._min_sample_size,
            "applied_optimizations": len(self._applied_optimizations),
        }
