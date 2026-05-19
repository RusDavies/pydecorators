# Decorator Composition

Python applies stacked decorators from the bottom up:

```python
@outer
@inner
def work():
    ...

# roughly means:
work = outer(inner(work))
```

That means the decorator closest to `def` sees the original function first. The decorator at the top wraps everything below it.

## Practical ordering rule

For reliability-style decorators, start with this order and change it only when you want different semantics:

```python
from useful_decorators import log_calls, measure_time, rate_limit, retry, validate_types


@measure_time(callback=timings.append)
@log_calls(logger=logger)
@rate_limit(calls=10, period=60)
@retry(attempts=3, delay=0.1, exceptions=(ConnectionError, TimeoutError))
@validate_types()
def call_dependency(user_id: str) -> str:
    return user_id
```

Read from the top as operational policy and from the bottom as execution flow:

1. `@validate_types` checks caller mistakes before operational wrappers do work.
2. `@retry` retries the dependency call after configured transient failures.
3. `@rate_limit` limits logical calls into the retrying operation.
4. `@log_calls` logs one outer call, not every internal retry attempt.
5. `@measure_time` measures the whole decorated operation, including waiting, retries, and logging overhead.

This is a default, not a law of physics. Unfortunately.

## Common choices

### Measure one whole operation

Put `@measure_time` near the top when you want user-visible latency for the whole operation:

```python
@measure_time(callback=timings.append)
@retry(attempts=3, delay=0.1)
def fetch_user(user_id: str) -> str:
    return user_id
```

The timing includes all retry attempts and retry sleeps.

### Measure each retry attempt

Put `@measure_time` below `@retry` when you want one timing event per attempt:

```python
@retry(attempts=3, delay=0.1)
@measure_time(callback=timings.append)
def fetch_user(user_id: str) -> str:
    return user_id
```

That can be useful for dependency diagnostics, but it also emits more events.

### Log one call instead of every attempt

Put `@log_calls` above `@retry` when logs should describe one logical operation:

```python
@log_calls(logger=logger)
@retry(attempts=3, delay=0.1)
def fetch_user(user_id: str) -> str:
    return user_id
```

Put `@log_calls` below `@retry` only when you intentionally want each attempt logged.

### Rate-limit logical operations

Put `@rate_limit` above `@retry` when one user call should consume one rate-limit slot even if retries happen internally:

```python
@rate_limit(calls=10, period=60)
@retry(attempts=3, delay=0.1)
def call_api() -> str:
    return "ok"
```

Put `@rate_limit` below `@retry` when each retry attempt should consume a slot. That is stricter and can be useful when protecting a fragile dependency.

### Circuit-breaker placement

For most service-client code, put `@circuit_breaker` outside retry so the breaker sees one logical operation failure after retries are exhausted:

```python
@circuit_breaker(failure_threshold=3, reset_timeout=30)
@retry(attempts=3, delay=0.1, exceptions=ConnectionError)
def call_api() -> str:
    return "ok"
```

Put `@circuit_breaker` inside retry only if each failed attempt should count toward opening the circuit. That opens faster and is usually more aggressive than people expect.

### Async timeout placement

`@timeout` supports async callables only. Put it outside retry when the whole operation has one deadline:

```python
@timeout(seconds=2)
@retry(attempts=3, delay=0.1)
async def fetch_user(user_id: str) -> str:
    return user_id
```

Put it inside retry when each attempt gets its own timeout budget:

```python
@retry(attempts=3, delay=0.1)
@timeout(seconds=2)
async def fetch_user(user_id: str) -> str:
    return user_id
```

The second form can run much longer overall because each retry gets a fresh timeout.

## Failure modes to watch for

Decorator order is not decorative. It changes what the system actually does.

- `@retry` outside `@rate_limit` means each retry attempt may consume a rate-limit slot.
  That can be correct when protecting a fragile dependency, but it can also exhaust the
  local allowance with one unlucky user call.
- `@timeout` inside `@retry` gives each attempt a fresh deadline. Three attempts with a
  two-second timeout can take roughly six seconds plus retry delays. That is not a
  two-second user experience; it is a small scheduling ambush.
- `@log_calls` below `@retry` logs every attempt. Useful for diagnosis, noisy in normal
  service logs, and especially tedious when an outage turns one error into a thousand
  identical little postcards from the crater.
- `@circuit_breaker` inside `@retry` counts each failed attempt toward opening the
  circuit. That opens faster, but it may also trip the breaker from one logical request
  instead of sustained dependency failure.

When changing order, name the semantic change in the review. "Looks cleaner" is not a
reliability argument.

## Dogfood finding

The local dogfood harness and external-project dogfood both worked without API changes. The main finding was documentation, not code: wrapper order needs to be explicit because `@retry`, `@rate_limit`, `@log_calls`, `@measure_time`, `@timeout`, and `@circuit_breaker` all have reasonable-but-different behavior depending on where they sit in the stack.


## Executable examples

Copy-pasteable stacking examples live in `docs/examples/composition_examples.py`
and are covered by `tests/test_docs_examples.py`. They exercise whole-operation
timing, one-logical-call logging, circuit-breaker placement, and async timeout
placement so composition guidance stays executable instead of ornamental.
