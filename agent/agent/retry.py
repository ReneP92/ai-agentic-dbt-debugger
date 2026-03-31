"""Retry helper for transient API errors.

Wraps an agent invocation with exponential backoff so that temporary
failures (overloaded, rate-limited, 5xx, network issues) are retried
automatically instead of crashing the pipeline.

Handles both raw Anthropic SDK exceptions (when they bubble up from
sub-agent calls inside @tool functions) and Strands-wrapped exceptions
(e.g. ModelThrottledException for 429s).
"""

import time

import anthropic
from strands.types.exceptions import ModelThrottledException

MAX_RETRIES = 6
BACKOFF_BASE = 2   # seconds: 5, 10, 20, 40, 60, 60 (capped)
INITIAL_DELAY = 5  # first retry starts at 5s
MAX_DELAY = 60     # cap so we don't wait forever


def is_retryable(exc: Exception) -> bool:
    """Return True if *exc* is a transient error worth retrying."""
    # Strands wraps 429 RateLimitError as ModelThrottledException
    if isinstance(exc, ModelThrottledException):
        return True

    # Raw Anthropic connection / timeout errors
    if isinstance(exc, anthropic.APIConnectionError):  # includes APITimeoutError
        return True

    # Raw Anthropic status errors: 429 (rate limit), 529 (overloaded), 5xx
    if isinstance(exc, anthropic.APIStatusError):
        if exc.status_code == 429 or exc.status_code >= 500:
            return True

        # SSE streaming edge case: Anthropic returns HTTP 200 to start the
        # stream, then sends an error event mid-stream.  The SDK constructs
        # a bare APIStatusError with status_code=200 (the original HTTP
        # status) but the body contains the real error type.  We inspect
        # the body to catch transient errors that arrive this way.
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            error_info = body.get("error", {})
            if isinstance(error_info, dict) and error_info.get("type") in (
                "overloaded_error",
                "api_error",
            ):
                return True

    return False


def invoke_with_retry(agent, prompt: str, *, label: str = "agent"):
    """Call ``agent(prompt)`` with exponential backoff on transient errors.

    Retries up to ``MAX_RETRIES`` times with delays of 2 s, 4 s, 8 s.
    Non-retryable exceptions (auth errors, bad requests, etc.) are raised
    immediately.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return agent(prompt)
        except Exception as exc:
            exc_type = type(exc).__name__
            status = getattr(exc, "status_code", None)
            retryable = is_retryable(exc)
            print(
                f"[{label}] Exception caught: {exc_type}"
                f" (status={status}, retryable={retryable})"
            )

            if not retryable or attempt == MAX_RETRIES:
                raise
            delay = min(MAX_DELAY, INITIAL_DELAY * (BACKOFF_BASE ** (attempt - 1)))
            print(f"[{label}] Transient API error (attempt {attempt}/{MAX_RETRIES}): {exc}")
            print(f"[{label}] Retrying in {delay}s...")
            time.sleep(delay)
