"""Tests for performance metrics."""

import pytest
from src.learning.outcome_tracker import OutcomeTracker, TaskOutcome, Outcome
from src.learning.performance_metrics import PerformanceMetrics, AgentScore
from src.agents.agent_registry import create_default_registry


def _record(tracker, agent_type, outcome=Outcome.SUCCESS, duration_ms=1000):
    tracker.record(TaskOutcome(
        task_id=f"t-{tracker.total_outcomes}",
        task_type="email",
        agent_id=f"{agent_type}-agent",
        agent_type=agent_type,
        outcome=outcome,
        duration_ms=duration_ms,
    ))


@pytest.fixture
def metrics():
    tracker = OutcomeTracker()
    registry = create_default_registry()
    return PerformanceMetrics(tracker, registry), tracker


class TestPerformanceMetrics:
    def test_score_agent_empty(self, metrics):
        pm, _ = metrics
        score = pm.score_agent("sales")
        assert score.reliability == 0.0
        assert score.composite == 0.0

    def test_score_agent_perfect(self, metrics):
        pm, tracker = metrics
        for _ in range(10):
            _record(tracker, "sales", Outcome.SUCCESS, 500)
        score = pm.score_agent("sales")
        assert score.reliability == 100.0
        assert score.composite > 50

    def test_score_agent_mixed(self, metrics):
        pm, tracker = metrics
        for _ in range(7):
            _record(tracker, "finance", Outcome.SUCCESS, 1000)
        for _ in range(3):
            _record(tracker, "finance", Outcome.FAILURE, 1000)
        score = pm.score_agent("finance")
        assert score.reliability == 70.0

    def test_score_all_agents(self, metrics):
        pm, tracker = metrics
        for _ in range(5):
            _record(tracker, "sales", Outcome.SUCCESS, 500)
        for _ in range(5):
            _record(tracker, "content", Outcome.SUCCESS, 2000)
        scores = pm.score_all_agents()
        # Should be sorted by composite (sales should score higher due to speed)
        assert len(scores) >= 2

    def test_to_dict(self, metrics):
        pm, tracker = metrics
        _record(tracker, "sales")
        score = pm.score_agent("sales")
        d = score.to_dict()
        assert "reliability" in d
        assert "composite" in d

    def test_swarm_health_empty(self, metrics):
        pm, _ = metrics
        health = pm.get_swarm_health()
        assert "overall_score" in health
        assert "recommendations" in health

    def test_swarm_health_with_data(self, metrics):
        pm, tracker = metrics
        for _ in range(10):
            _record(tracker, "sales", Outcome.SUCCESS)
        for _ in range(10):
            _record(tracker, "content", Outcome.FAILURE)
        health = pm.get_swarm_health()
        assert health["total_tasks"] == 20
        # Content agent should trigger a recommendation
        assert any("content" in r.lower() for r in health["recommendations"])

    def test_speed_score_fast_agent(self, metrics):
        pm, tracker = metrics
        for _ in range(5):
            _record(tracker, "sales", Outcome.SUCCESS, 100)  # Very fast
        score = pm.score_agent("sales")
        assert score.speed > 90  # Near perfect speed

    def test_speed_score_slow_agent(self, metrics):
        pm, tracker = metrics
        for _ in range(5):
            _record(tracker, "finance", Outcome.SUCCESS, 50000)  # Very slow
        score = pm.score_agent("finance")
        assert score.speed < 30
