# `@retry`

`@retry` retries a sync or async function when configured exception types are raised. It is configured-only because retry policy should be explicit at the call site.

```python
from useful_decorators import retry


@retry(attempts=3, delay=0.25, backoff=2, exceptions=TimeoutError)
def fetch_user(user_id: str) -> dict[str, object]:
    ...
```

## Parameters

- `attempts`: total attempts, including the first call. Must be greater than zero.
- `delay`: initial delay between failed attempts. Defaults to `0`.
- `backoff`: multiplier applied to the delay after each retry. Defaults to `1`, meaning fixed delay.
- `max_delay`: optional cap for exponential backoff.
- `jitter`: optional random additive jitter, from `0` to `jitter`, applied to each sleep.
- `exceptions`: exception type or tuple of exception types that should be considered retryable. Defaults to `Exception`.
- `retry_if`: optional predicate receiving the caught exception. Return `False` to stop retrying even if attempts remain.
- `before_attempt`: optional hook called with the 1-based attempt number before each call.
- `after_attempt`: optional hook called with the 1-based attempt number and either the caught exception or `None` after success.
- `sleep`: injectable sync or async sleep callable for tests and custom schedulers.

Invalid configuration raises `ConfigurationError` at decoration time.

## Behavior

The first call counts as attempt 1. If it succeeds, no sleep occurs. If a configured exception is raised and attempts remain, `@retry` sleeps and tries again. When attempts are exhausted, the last exception is re-raised unchanged.

Non-matching exceptions are never retried. Predicate-rejected exceptions are also re-raised immediately.

`@retry` preserves wrapped function metadata and supports async functions with the same policy shape. Test suites should inject `sleep` so retry tests stay fast instead of taking a nap like a tiny unreliable server.

## Examples

Fixed delay:

```python
@retry(attempts=3, delay=0.1, exceptions=ConnectionError)
def call_service() -> str:
    ...
```

Exponential backoff with a cap:

```python
@retry(attempts=4, delay=0.5, backoff=2, max_delay=2.0)
def refresh_cache() -> None:
    ...
```

Predicate-based retry:

```python
def retry_transient(exc: BaseException) -> bool:
    return "transient" in str(exc).lower()


@retry(attempts=3, retry_if=retry_transient)
def run_job() -> None:
    ...
```
