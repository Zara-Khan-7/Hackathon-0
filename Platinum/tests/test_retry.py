"""Tests for the exponential backoff retry decorator."""

import pytest
import time

from src.utils.retry import with_retry, RetryExhausted


class TestWithRetry:
    """Test the @with_retry decorator."""

    def test_success_on_first_try(self):
        call_count = 0

        @with_retry(max_attempts=3)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_success_after_retry(self):
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_exhausted_raises(self):
        call_count = 0

        @with_retry(max_attempts=2, base_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("always fails")

        with pytest.raises(RetryExhausted) as exc_info:
            always_fail()

        assert exc_info.value.attempts == 2
        assert "always fails" in str(exc_info.value.last_error)
        assert call_count == 2

    def test_backoff_timing(self):
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.05, backoff_factor=2.0)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        start = time.time()
        result = fail_twice()
        elapsed = time.time() - start

        assert result == "ok"
        # Should have waited ~0.05 + ~0.10 = ~0.15s (with some tolerance)
        assert elapsed >= 0.1
        assert elapsed < 1.0

    def test_preserves_function_name(self):
        @with_retry(max_attempts=2)
        def my_function():
            return True

        assert my_function.__name__ == "my_function"

    def test_passes_args_and_kwargs(self):
        @with_retry(max_attempts=2)
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2) == 3
        assert add(1, 2, extra=10) == 13
