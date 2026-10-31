"""Small, bounded HTTP retry helpers for external transcription services."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import os
import time

import requests


RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def _retry_after_seconds(value: str | None, maximum: float) -> float | None:
    """Parse Retry-After as seconds or an HTTP date, bounded by maximum."""
    if not value:
        return None

    try:
        delay = float(value.strip())
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            delay = (retry_at - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None

    return max(0.0, min(delay, maximum))


def post_with_retry(
    url: str,
    *,
    timeout: tuple[float, float] = (10, 120),
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    max_backoff_seconds: float = 15.0,
    retry_statuses: set[int] | None = None,
    **kwargs,
):
    """POST with bounded retries for timeouts, connection errors and transient HTTP status codes.

    Non-retryable responses are returned immediately so callers can report the
    provider's useful 4xx error. After the final attempt, the final response is
    returned or the final requests exception is re-raised.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if timeout is None:
        raise ValueError("A finite HTTP timeout is required")

    retry_statuses = retry_statuses or RETRYABLE_STATUS_CODES
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, timeout=timeout, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exception = exc
            if attempt >= max_attempts:
                raise
            delay = min(backoff_seconds * (2 ** (attempt - 1)), max_backoff_seconds)
            time.sleep(delay)
            continue

        if response.status_code not in retry_statuses or attempt >= max_attempts:
            return response

        retry_after = _retry_after_seconds(
            response.headers.get("Retry-After"), max_backoff_seconds
        )
        delay = retry_after if retry_after is not None else min(
            backoff_seconds * (2 ** (attempt - 1)), max_backoff_seconds
        )
        time.sleep(delay)

    if last_exception is not None:
        raise last_exception
    raise RuntimeError("HTTP retry loop ended unexpectedly")


def provider_max_workers(
    env_name: str = "SARVAM_MAX_WORKERS",
    default: int = 3,
    maximum: int = 8,
) -> int:
    """Read a safe, bounded worker count for provider requests."""
    try:
        requested = int(os.getenv(env_name, str(default)))
    except (TypeError, ValueError):
        requested = default
    return max(1, min(requested, maximum))
