"""Performance Metrics — agent and swarm performance scoring.

Provides real-time and historical performance metrics for the
Dashboard and self-improving loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agents.agent_registry import AgentRegistry
from src.learning.outcome_tracker import OutcomeTracker, Outcome


@dataclass
class AgentScore:
    """Composite performance score for an agent."""
    agent_type: str
    reliability: float     # success rate (0-100)
    speed: float           # inverse of avg duration, normalized (0-100)
    volume: float          # tasks handled relative to peers (0-100)
    composite: float       # weighted average

    def to_dict(self) -> dict:
        return {
            "agent_type": self.agent_type,
            "reliability": round(self.reliability, 1),
            "speed": round(self.speed, 1),
            "volume": round(self.volume, 1),
            "composite": round(self.composite, 1),
        }


class PerformanceMetrics:
    """Calculates performance scores for agents and the swarm."""

    # Weights for composite score
    RELIABILITY_WEIGHT = 0.5
    SPEED_WEIGHT = 0.3
    VOLUME_WEIGHT = 0.2

    def __init__(self, tracker: OutcomeTracker, registry: AgentRegistry):
        self._tracker = tracker
        self._registry = registry

    def score_agent(self, agent_type: str) -> AgentScore:
        """Calculate composite score for an agent type."""
        outcomes = self._tracker.get_outcomes(agent_type=agent_type)

        if not outcomes:
            return AgentScore(
                agent_type=agent_type,
                reliability=0.0,
                speed=0.0,
                volume=0.0,
                composite=0.0,
            )

        # Reliability: success rate * 100
        successes = sum(1 for o in outcomes if o.outcome == Outcome.SUCCESS)
        reliability = (successes / len(outcomes)) * 100

        # Speed: normalized inverse of avg duration (lower is better)
        avg_ms = sum(o.duration_ms for o in outcomes) / len(outcomes)
        # Scale: 0ms = 100, 60000ms+ = 0
        speed = max(0, min(100, 100 - (avg_ms / 600)))

        # Volume: relative to total outcomes
        total = self._tracker.total_outcomes or 1
        volume = min(100, (len(outcomes) / total) * 100 * len(self._get_agent_types()))

        composite = (
            reliability * self.RELIABILITY_WEIGHT +
            speed * self.SPEED_WEIGHT +
            volume * self.VOLUME_WEIGHT
        )

        return AgentScore(
            agent_type=agent_type,
            reliability=reliability,
            speed=speed,
            volume=volume,
            composite=composite,
        )

    def score_all_agents(self) -> list[AgentScore]:
        """Score all agent types, sorted by composite score."""
        agent_types = self._get_agent_types()
        scores = [self.score_agent(at) for at in agent_types]
        scores.sort(key=lambda s: s.composite, reverse=True)
        return scores

    def get_swarm_health(self) -> dict:
        """Overall swarm health metrics."""
        scores = self.score_all_agents()
        if not scores:
            return {
                "overall_score": 0.0,
                "agent_scores": [],
                "total_tasks": 0,
                "recommendations": ["No data yet."],
            }

        overall = sum(s.composite for s in scores) / len(scores)
        recommendations = []

        for s in scores:
            if s.reliability < 70:
                recommendations.append(
                    f"{s.agent_type}: Low reliability ({s.reliability:.0f}%). "
                    f"Review error patterns."
                )
            if s.speed < 30:
                recommendations.append(
                    f"{s.agent_type}: Slow performance ({s.speed:.0f}/100). "
                    f"Consider optimization."
                )

        return {
            "overall_score": round(overall, 1),
            "agent_scores": [s.to_dict() for s in scores],
            "total_tasks": self._tracker.total_outcomes,
            "recommendations": recommendations or ["All agents performing well."],
        }

    def _get_agent_types(self) -> list[str]:
        """Get unique agent types from outcomes and registry."""
        types = set()
        for agent_stats in self._registry.list_agents():
            types.add(agent_stats["type"])
        for outcome in self._tracker.get_outcomes():
            types.add(outcome.agent_type)
        return sorted(types)
