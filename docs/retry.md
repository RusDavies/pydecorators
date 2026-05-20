# `@retry`

`@retry` retries a sync or async function when configured exception types are raised. It is configured-only because retry policy should be explicit at the call site.

```python
from pydecorators import retry


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
- `before_attempt`: optional hook called with the 1-based attempt number before each call. Async retry wrappers await the hook if it returns an awaitable.
- `after_attempt`: optional hook called with the 1-based attempt number and either the caught exception or `None` after success. Async retry wrappers await the hook if it returns an awaitable.
- `sleep`: injectable sync or async sleep callable for tests and custom schedulers.

Invalid configuration raises `ConfigurationError` at decoration time.

## Behavior

The first call counts as attempt 1. If it succeeds, no sleep occurs. If a configured exception is raised and attempts remain, `@retry` sleeps and tries again. When attempts are exhausted, the last exception is re-raised unchanged.

Non-matching exceptions are never retried. Predicate-rejected exceptions are also re-raised immediately.

`@retry` preserves wrapped function metadata and supports async functions with the same policy shape. Test suites should inject `sleep` so retry tests stay fast instead of taking a nap like a tiny unreliable server.

## Idempotency guidance

Only retry operations that are safe to run more than once, or operations protected by an idempotency key, transaction boundary, compare-and-swap guard, or similar duplicate-prevention mechanism.

Good retry candidates include reads, cache refreshes, health checks, and dependency calls where the remote side treats duplicate requests as the same logical operation. Risky candidates include payments, account creation, email sending, order submission, inventory mutation, and anything that makes the outside world different each time it runs.

If a side-effecting operation must be retried, make the idempotency key part of the operation being retried and log enough context to reconcile duplicate attempts. Do not hide non-idempotent business logic behind `@retry` just because transient failures are annoying. They are annoying; so are duplicate invoices.

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


## Executable examples

Copy-pasteable examples live in `docs/examples/retry_examples.py` and are covered
by `tests/test_docs_examples.py`. They demonstrate transient success,
predicate-rejected exceptions, and async retry with injected sleep functions so
the examples do not pause the test suite like an obedient little metronome.


## Executable idempotency examples

Side-effecting retry recipes live in `docs/examples/retry_idempotency_examples.py`
and are covered by `tests/test_docs_examples.py`. The examples keep the important
rule concrete: retry reads freely, but retry mutations only when the operation
has a real duplicate-prevention mechanism such as an idempotency key.
