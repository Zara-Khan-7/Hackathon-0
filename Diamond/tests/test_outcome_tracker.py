"""Tests for outcome tracker and self-improving loop."""

import pytest
from src.learning.outcome_tracker import OutcomeTracker, TaskOutcome, Outcome
from src.learning.prompt_optimizer import PromptOptimizer


def _make_outcome(agent_type="sales", task_type="email",
                  outcome=Outcome.SUCCESS, duration_ms=1000,
                  details=""):
    return TaskOutcome(
        task_id=f"task-{id(outcome)}",
        task_type=task_type,
        agent_id=f"{agent_type}-agent",
        agent_type=agent_type,
        outcome=outcome,
        duration_ms=duration_ms,
        details=details,
    )


class TestOutcomeTracker:
    def test_record_and_count(self):
        tracker = OutcomeTracker()
        tracker.record(_make_outcome())
        assert tracker.total_outcomes == 1

    def test_success_rate(self):
        tracker = OutcomeTracker()
        tracker.record(_make_outcome(outcome=Outcome.SUCCESS))
        tracker.record(_make_outcome(outcome=Outcome.SUCCESS))
        tracker.record(_make_outcome(outcome=Outcome.FAILURE))
        assert abs(tracker.success_rate() - 0.6667) < 0.01

    def test_success_rate_empty(self):
        tracker = OutcomeTracker()
        assert tracker.success_rate() == 0.0

    def test_filter_by_agent_type(self):
        tracker = OutcomeTracker()
        tracker.record(_make_outcome(agent_type="sales"))
        tracker.record(_make_outcome(agent_type="finance"))
        results = tracker.get_outcomes(agent_type="sales")
        assert len(results) == 1

    def test_filter_by_task_type(self):
        tracker = OutcomeTracker()
        tracker.record(_make_outcome(task_type="email"))
        tracker.record(_make_outcome(task_type="payment"))
        results = tracker.get_outcomes(task_type="email")
        assert len(results) == 1

    def test_avg_duration(self):
        tracker = OutcomeTracker()
        tracker.record(_make_outcome(duration_ms=1000))
        tracker.record(_make_outcome(duration_ms=3000))
        assert tracker.avg_duration() == 2000.0

    def test_failure_patterns(self):
        tracker = OutcomeTracker()
        for _ in range(3):
            tracker.record(_make_outcome(
                agent_type="sales", task_type="email",
                outcome=Outcome.FAILURE, details="timeout"
            ))
        patterns = tracker.failure_patterns(min_count=3)
        assert len(patterns) == 1
        assert patterns[0]["failure_count"] == 3

    def test_get_agent_performance(self):
        tracker = OutcomeTracker()
        tracker.record(_make_outcome(agent_type="sales", outcome=Outcome.SUCCESS))
        tracker.record(_make_outcome(agent_type="sales", outcome=Outcome.FAILURE))
        perf = tracker.get_agent_performance()
        assert len(perf) == 1
        assert perf[0]["total_tasks"] == 2
        assert perf[0]["success_rate"] == 0.5

    def test_persist_to_file(self, tmp_path):
        log_path = tmp_path / "outcomes.jsonl"
        tracker = OutcomeTracker(log_path=log_path)
        tracker.record(_make_outcome())
        assert log_path.exists()
        content = log_path.read_text()
        assert "success" in content

    def test_last_n_filter(self):
        tracker = OutcomeTracker()
        for i in range(10):
            tracker.record(_make_outcome())
        results = tracker.get_outcomes(last_n=3)
        assert len(results) == 3


class TestPromptOptimizer:
    def test_analyze_empty(self):
        tracker = OutcomeTracker()
        optimizer = PromptOptimizer(tracker, min_sample_size=5)
        optimizations = optimizer.analyze()
        assert len(optimizations) == 0

    def test_analyze_low_success_rate(self):
        tracker = OutcomeTracker()
        for _ in range(12):
            tracker.record(_make_outcome(outcome=Outcome.FAILURE))
        for _ in range(3):
            tracker.record(_make_outcome(outcome=Outcome.SUCCESS))

        optimizer = PromptOptimizer(tracker, min_sample_size=10)
        optimizations = optimizer.analyze()
        assert len(optimizations) > 0
        assert any("low success rate" in o.recommendation.lower() for o in optimizations)

    def test_analyze_failure_pattern(self):
        tracker = OutcomeTracker()
        for _ in range(5):
            tracker.record(_make_outcome(
                outcome=Outcome.FAILURE, details="API timeout"
            ))

        optimizer = PromptOptimizer(tracker, min_sample_size=2)
        optimizations = optimizer.analyze()
        assert any("recurring failure" in o.recommendation.lower() for o in optimizations)

    def test_apply_optimization(self):
        tracker = OutcomeTracker()
        optimizer = PromptOptimizer(tracker)
        from src.learning.prompt_optimizer import Optimization
        opt = Optimization(
            agent_type="sales", task_type="email",
            recommendation="Improve email templates",
            confidence=0.8, based_on_samples=20,
        )
        optimizer.apply(opt)
        assert optimizer.get_stats()["applied_optimizations"] == 1

    def test_slow_agent_detection(self):
        tracker = OutcomeTracker()
        for _ in range(15):
            tracker.record(_make_outcome(duration_ms=50000))  # 50s per task

        optimizer = PromptOptimizer(tracker, min_sample_size=10)
        optimizations = optimizer.analyze()
        assert any("slow" in o.recommendation.lower() for o in optimizations)
