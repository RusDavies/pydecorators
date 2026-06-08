# `@rate_limit`

`@rate_limit` limits how often a sync or async function may be called. It uses a sliding-window policy so old calls expire continuously rather than only at fixed wall-clock boundaries.

```python
from pydecorators import rate_limit


@rate_limit(calls=10, period=60)
def call_api(path: str) -> str:
    ...
```

## Parameters

- `calls`: number of calls allowed per window. Must be greater than zero.
- `period`: window length in seconds. Must be greater than zero.
- `key`: optional callable that receives the wrapped function arguments and returns a hashable bucket key. When omitted, all calls share one global bucket.
- `mode`: either `"raise"` or `"block"`. Defaults to `"raise"`.
- `clock`: injectable monotonic clock for tests.
- `sleep`: injectable sync or async sleep callable for block mode and tests.
- `interprocess`: opt-in same-host, multi-process coordination. Defaults to `False`.
- `storage_path`: SQLite database path required when `interprocess=True`.
- `namespace`: optional shared bucket namespace. Defaults to the wrapped function's module and qualified name.

Invalid configuration raises `ConfigurationError` at decoration time.

## Modes

In `"raise"` mode, an exceeded call raises `RateLimitExceeded`. The exception exposes a machine-readable `retry_after` value in seconds and includes the same retry-after hint in its message.

In `"block"` mode, the wrapper sleeps until the oldest call leaves the sliding window, then tries again. Tests should inject `clock` and `sleep` so they do not actually wait around like patient little potatoes.

## Keyed rate limits

Use `key=` to isolate independent buckets, such as per tenant, per user, or per API credential:

```python
@rate_limit(calls=5, period=60, key=lambda tenant_id, path: tenant_id)
def call_tenant_api(tenant_id: str, path: str) -> str:
    ...
```

The key function must return a hashable value. Key generation errors propagate to the caller.

## Async support

Async functions use the same sliding-window policy. In block mode, the default async path uses `asyncio.sleep`; callers can inject a custom async sleep function for tests or schedulers.

## Interprocess rate limits

By default, `@rate_limit` is process-local. Set `interprocess=True` and provide a SQLite `storage_path` when multiple local Python processes should share the same sliding-window buckets:

```python
@rate_limit(
    calls=100,
    period=60,
    key=lambda user_id: user_id,
    interprocess=True,
    storage_path="/var/tmp/my-service-rate-limits.sqlite3",
    namespace="third-party-api:v1",
)
def call_api(user_id: str) -> str:
    ...
```

Interprocess mode coordinates processes on the same host through SQLite transactions. It does not hold the database lock while sleeping in `"block"` mode. Bucket keys are serialized and hashed before storage, so custom keys used with `interprocess=True` must be pickle-serializable as well as hashable.

Use an explicit `namespace` when multiple decorated functions should intentionally share one allowance. Omit it when each decorated function should have its own bucket namespace.

Interprocess mode is not a multi-host distributed quota system. Containers or services on different hosts need an external shared service such as Redis, Postgres, or the protected API's own quota signals.

## Idempotency and side effects

`@rate_limit` does not make an operation idempotent. It only controls how often the wrapped function is allowed to start in the configured process-local or same-host interprocess bucket.

Use rate limiting to protect dependencies, quotas, local tools, and best-effort workloads. For side-effecting operations such as payments, order submission, account creation, or message delivery, keep the operation's own idempotency controls in place. A blocked or rejected call might be retried by the caller, and a distributed system might run the same logical request in another process that has a separate in-memory bucket.

If the protected dependency has its own retry-after or quota headers, prefer feeding those signals into caller behavior instead of assuming this local limiter has a complete picture. Local politeness is useful; it is not a treaty with the universe.

## Failure modes to watch for

Rate limiting is about admission control. It does not guarantee fairness, idempotency,
or distributed correctness by itself.

- The default bucket is global for the decorated function. One noisy tenant or caller can
  consume the allowance for everyone unless you provide a `key=` function.
- Keyed buckets are only as good as the key. A key that ignores tenant, credential, or
  endpoint boundaries can accidentally couple workloads that should be isolated.
- In `"block"` mode, callers wait inside the wrapper. That can be fine for scripts and
  small tools, but in a service it can tie up workers and turn quota pressure into
  latency pressure.
- In `"raise"` mode, callers need a plan for `RateLimitExceeded.retry_after`. Ignoring
  it usually creates a tight retry loop, which is just a denial-of-service attack with
  better variable names.
- The default limiter is in-process. Multiple processes each have their own bucket unless
  `interprocess=True` points them at the same SQLite database and namespace.
- Interprocess mode is same-host coordination, not distributed consensus. Multiple hosts,
  independent containers without shared storage, or serverless instances still need an
  external quota mechanism.

## Notes

The default limiter is in-process. It is suitable for scripts, local tools, tests, and single-process services. Interprocess mode adds same-host SQLite coordination for multiple local workers. Neither mode is a distributed quota system across multiple hosts.


## Executable examples

Copy-pasteable examples live in `docs/examples/rate_limit_examples.py` and are
covered by `tests/test_docs_examples.py`. They use an injectable clock and sleep
function so raise-mode, keyed-bucket, and block-mode behavior can be demonstrated
without real waiting.
