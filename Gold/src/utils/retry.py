"""Exponential backoff retry decorator for resilient MCP and API calls.

Usage:
    @with_retry(max_attempts=3, backoff_factor=2)
    def call_external_api():
        ...
"""

import functools
import logging
import time

logger = logging.getLogger("ai_employee")


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, func_name: str, attempts: int, last_error: Exception):
        self.func_name = func_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"{func_name} failed after {attempts} attempts: {last_error}"
        )


def with_retry(max_attempts: int = 3, backoff_factor: float = 2.0, base_delay: float = 1.0):
    """Decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including first try).
        backoff_factor: Multiplier for delay between retries (1s, 2s, 4s...).
        base_delay: Initial delay in seconds before first retry.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_attempts:
                        logger.error(
                            f"[Retry] {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise RetryExhausted(func.__name__, max_attempts, e) from e

                    delay = base_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(
                        f"[Retry] {func.__name__} attempt {attempt}/{max_attempts} "
                        f"failed ({e}), retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            raise RetryExhausted(func.__name__, max_attempts, last_error)

        return wrapper

    return decorator
