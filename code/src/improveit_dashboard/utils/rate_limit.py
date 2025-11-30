"""Rate limit handling for GitHub API."""

import time
from typing import Any

from improveit_dashboard.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is critically low."""

    def __init__(self, message: str, reset_timestamp: int = 0):
        super().__init__(message)
        self.reset_timestamp = reset_timestamp


class RateLimitHandler:
    """Handles GitHub API rate limiting.

    Monitors rate limit headers and pauses when limit is low.
    """

    def __init__(self, threshold: int = 100, critical_threshold: int = 10):
        """Initialize rate limit handler.

        Args:
            threshold: Pause when remaining calls fall below this
            critical_threshold: Abort when remaining falls below this
        """
        self.threshold = threshold
        self.critical_threshold = critical_threshold
        self.remaining = 5000
        self.limit = 5000
        self.reset_timestamp = 0

    def check_and_wait(self, response: Any) -> None:
        """Check rate limit from response headers and wait if needed.

        Args:
            response: requests.Response object

        Raises:
            RateLimitError: If rate limit is critically low
        """
        headers = response.headers

        # Parse rate limit headers
        self.remaining = int(headers.get("X-RateLimit-Remaining", self.remaining))
        self.limit = int(headers.get("X-RateLimit-Limit", self.limit))
        self.reset_timestamp = int(headers.get("X-RateLimit-Reset", 0))

        logger.debug(
            f"Rate limit: {self.remaining}/{self.limit} remaining, resets at {self.reset_timestamp}"
        )

        # Critical threshold - abort
        if self.remaining < self.critical_threshold:
            wait_seconds = max(0, self.reset_timestamp - int(time.time()))
            raise RateLimitError(
                f"Rate limit critically low ({self.remaining}), resets in {wait_seconds}s",
                reset_timestamp=self.reset_timestamp,
            )

        # Low threshold - wait for reset
        if self.remaining < self.threshold:
            wait_seconds = max(0, self.reset_timestamp - int(time.time()))
            if wait_seconds > 0:
                logger.warning(
                    f"Rate limit low ({self.remaining}), waiting {wait_seconds}s until reset"
                )
                time.sleep(wait_seconds + 1)  # Add 1s buffer

    def update_from_response(self, response: Any) -> None:
        """Update rate limit info from response without waiting.

        Useful for non-blocking updates.

        Args:
            response: requests.Response object
        """
        headers = response.headers
        self.remaining = int(headers.get("X-RateLimit-Remaining", self.remaining))
        self.limit = int(headers.get("X-RateLimit-Limit", self.limit))
        self.reset_timestamp = int(headers.get("X-RateLimit-Reset", 0))

    def get_status(self) -> dict[str, int]:
        """Get current rate limit status.

        Returns:
            Dict with remaining, limit, and reset_timestamp
        """
        return {
            "remaining": self.remaining,
            "limit": self.limit,
            "reset_timestamp": self.reset_timestamp,
        }
