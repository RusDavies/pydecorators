# `@circuit_breaker`

`@circuit_breaker` stops calling a failing dependency after repeated failures, waits for a reset timeout, then allows one half-open probe call.

```python
from useful_decorators import circuit_breaker


@circuit_breaker(failure_threshold=3, reset_timeout=30)
def fetch_customer(customer_id: str) -> dict[str, object]:
    return api.fetch_customer(customer_id)
```

## States

- `closed`: calls run normally; failures are counted.
- `open`: calls are rejected with `CircuitBreakerOpen` until the reset timeout elapses.
- `half_open`: one probe call is allowed after the reset timeout.
  - success closes the circuit and resets the failure count.
  - failure reopens the circuit immediately.

## Parameters

- `failure_threshold`: number of counted failures required to open the circuit. Defaults to `3`.
- `reset_timeout`: seconds to keep the circuit open before allowing a half-open probe. Defaults to `30.0`.
- `exceptions`: non-empty tuple of exception types that count as failures. Defaults to `(Exception,)`.
- `exception_filter`: optional predicate receiving the exception; return `False` to ignore it.
- `clock`: injectable clock for deterministic tests.

Invalid configuration raises `ConfigurationError` at decoration time.

## Sync and async support

Both sync and async functions are supported. State is stored in the decorated function closure, so each decorated function gets its own in-process circuit. State transitions are guarded by a re-entrant lock for threaded callers within one process.

## State inspection

Decorated functions expose two small inspection helpers:

- `wrapped.circuit_state()` returns the current `CircuitState`, promoting `OPEN` to `HALF_OPEN` first if the reset timeout has elapsed.
- `wrapped.circuit_reset_after()` returns remaining seconds while open, or `None` when the circuit is closed or half-open.

These helpers are for logs, health checks, and tests. They are snapshots, not synchronization primitives; another caller can change the circuit immediately after inspection, because time and concurrency remain rude.

## Example: service client

```python
from useful_decorators import CircuitBreakerOpen, circuit_breaker


@circuit_breaker(failure_threshold=2, reset_timeout=10, exceptions=(TimeoutError, ConnectionError))
def call_vendor_api() -> str:
    return vendor.fetch()

try:
    payload = call_vendor_api()
except CircuitBreakerOpen:
    payload = "cached fallback"
```

## Limitations

This is an in-process circuit breaker. It is not shared across processes, containers, or hosts. For distributed systems, pair it with service-level timeouts, retries, backoff, and observability. Software reliability: one decorator helps; it does not replace architecture, no matter how much we squint at it.


## Executable examples

Copy-pasteable examples live in `docs/examples/circuit_breaker_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate open-circuit fallback,
half-open recovery, and async use with an injectable clock for deterministic output.
