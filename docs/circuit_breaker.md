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

## Failure modes to watch for

A circuit breaker protects callers from repeatedly hitting a failing dependency. It can
also make a bad threshold look like wisdom, so configure it deliberately.

- A threshold that is too low can open the circuit during a brief network wobble. That
  fails fast, but it may also deny calls while the dependency is already healthy again.
- A reset timeout that is too short can create probe storms against a sick dependency.
  Too long, and recovery is delayed for no useful reason. Pick a value that matches the
  dependency's failure and recovery pattern, not the nearest round number.
- Catching `CircuitBreakerOpen` and immediately calling the same dependency through a
  different path defeats the point. If there is a fallback, make it genuinely separate:
  cached data, degraded response, queued work, or a clear failure to the caller.
- The breaker state is local to one decorated function in one process. In a scaled
  service, different workers can disagree about whether the circuit is open. That is not
  a bug in this decorator; it is the operating model.
- Placing the breaker inside `@retry` counts individual attempts. Placing it outside
  counts logical operations after retries are exhausted. Choose the failure signal you
  actually want.


## Executable examples

Copy-pasteable examples live in `docs/examples/circuit_breaker_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate open-circuit fallback,
half-open recovery, and async use with an injectable clock for deterministic output.
