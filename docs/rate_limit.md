# `@rate_limit`

`@rate_limit` limits how often a sync or async function may be called. It uses a sliding-window policy so old calls expire continuously rather than only at fixed wall-clock boundaries.

```python
from pydecorators import CalendarRateLimitWindow, RateLimitWindow, rate_limit


@rate_limit(calls=10, period=60)
def call_api(path: str) -> str:
    ...
```

Use `windows=` when a dependency has more than one quota that must all be respected:

```python
@rate_limit(
    windows=[
        RateLimitWindow(calls=8, period=60, name="minute"),
        RateLimitWindow(calls=800, period=24 * 60 * 60, name="rolling-day"),
        RateLimitWindow(calls=4000, period=7 * 24 * 60 * 60, name="rolling-week"),
    ],
)
def call_api(path: str) -> str:
    ...
```

## Parameters

- `calls`: number of calls allowed per window. Must be greater than zero. Required when `windows` is omitted.
- `period`: window length in seconds. Must be greater than zero. Required when `windows` is omitted.
- `windows`: optional sequence of `RateLimitWindow(calls, period, name=None)`, `CalendarRateLimitWindow(calls, unit, name=None, timezone="UTC", week_start="monday")`, or `(calls, period)` tuples, for multi-window limits. Do not combine with `calls`/`period`.
- `key`: optional callable that receives the wrapped function arguments and returns a hashable bucket key. When omitted, all calls share one global bucket.
- `mode`: either `"raise"` or `"block"`. Defaults to `"raise"`.
- `clock`: injectable monotonic clock for tests.
- `sleep`: injectable sync or async sleep callable for block mode and tests.
- `interprocess`: opt-in same-host, multi-process coordination. Defaults to `False`.
- `storage_path`: SQLite database path required when `interprocess=True`.
- `namespace`: optional shared bucket namespace. Defaults to the wrapped function's module and qualified name.
- `distributed`: opt-in Redis-backed multi-host coordination. Defaults to `False`.
- `redis_client`: Redis-compatible client with an `eval()` method, used when `distributed=True`.
- `redis_url`: Redis URL used to construct a client when `distributed=True`. Requires installing `blakemere-wraptools[redis]`.
- `redis_key_prefix`: required Redis key prefix for distributed rate-limit state.

Invalid configuration raises `ConfigurationError` at decoration time.

`calls` and `period` are shorthand for one sliding window. This keeps existing code working while allowing new code to express multiple windows explicitly.

## Multiple windows

When `windows=` is provided, every call must fit inside every configured sliding window. The wrapper reserves capacity in all windows only after all windows pass. That all-or-nothing behavior matters: a call rejected by the daily window must not accidentally consume the minute window.

```python
@rate_limit(
    windows=[
        RateLimitWindow(calls=8, period=60, name="minute"),
        RateLimitWindow(calls=800, period=24 * 60 * 60, name="day"),
        RateLimitWindow(calls=4000, period=7 * 24 * 60 * 60, name="week"),
    ],
    mode="raise",
)
def call_vendor_api(path: str) -> str:
    ...
```

For `mode="raise"`, `RateLimitExceeded.retry_after` is the longest wait required by any exceeded window, because that is the earliest time the call can satisfy the full policy. For `mode="block"`, the wrapper sleeps for that same limiting delay and retries.

Window `name` values are optional. They provide stable storage identifiers for interprocess and distributed modes and make configuration easier to read. When omitted, the decorator derives a stable internal identifier from the window index and values. A single-window `windows=[...]` configuration uses the same storage identifier as the legacy `calls=`/`period=` shorthand so existing SQLite state remains compatible.

`RateLimitWindow` limits are sliding windows. `period=24 * 60 * 60` means a rolling 24-hour window, not a calendar day reset at midnight.

## Calendar-aligned windows

Use `CalendarRateLimitWindow` when the quota resets on a wall-clock boundary such as the start of a day or week:

```python
@rate_limit(
    windows=[
        RateLimitWindow(calls=8, period=60, name="minute"),
        CalendarRateLimitWindow(calls=800, unit="day", name="day", timezone="UTC"),
        CalendarRateLimitWindow(calls=4000, unit="week", name="week", timezone="UTC"),
    ],
)
def call_vendor_api(path: str) -> str:
    ...
```

Supported calendar units are `"minute"`, `"hour"`, `"day"`, and `"week"`. Calendar weeks start on Monday by default. Use `week_start="sunday"` for Sunday-start weeks.

Calendar windows use IANA time zone names through Python's standard `zoneinfo` module. The default is `"UTC"`. Pick the time zone that matches the upstream quota contract, not necessarily the server's local time zone.

When any calendar window is configured and `clock` is omitted, `@rate_limit` uses wall-clock Unix time so it can compute calendar boundaries. Pure sliding-window configurations continue to use a monotonic clock by default. Tests for calendar windows should inject a clock that returns Unix timestamps.

Calendar windows are fixed wall-clock buckets. A daily calendar window with `timezone="America/Toronto"` resets at Toronto midnight, including daylight-saving transitions. It is deliberately separate from a rolling 24-hour `RateLimitWindow` because those are different quota contracts and lying about time is how software summons demons.

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

Interprocess mode is not a multi-host distributed quota system. Containers or services on different hosts need distributed mode, another external shared service, or the protected API's own quota signals.

## Distributed Redis rate limits

Set `distributed=True` and provide either a Redis client or Redis URL when workers on multiple hosts should share a rate-limit bucket:

```python
@rate_limit(
    calls=100,
    period=60,
    key=lambda user_id: user_id,
    distributed=True,
    redis_url="redis://redis.example.internal:6379/0",
    redis_key_prefix="my-service:v1",
    namespace="third-party-api:v1",
)
def call_api(user_id: str) -> str:
    ...
```

Redis mode uses an atomic Lua script over sorted-set state, so pruning expired entries, checking capacity across every configured window, and reserving an admitted call happen as one Redis operation. It does not import `redis-py` unless `redis_url` construction is used; pass `redis_client=` if your application already owns Redis client lifecycle.

Use a stable, application-specific `redis_key_prefix` so independent services do not share quota state by accident. The prefix must not contain whitespace or Redis glob metacharacters. As with interprocess mode, custom bucket keys must be pickle-serializable as well as hashable because the stored Redis key uses a digest of the bucket key.

Redis-backed limiting coordinates callers that can reach the same Redis deployment. It still is not a complete fairness, identity, billing, or abuse-prevention system by itself.

The test suite includes live Redis integration coverage gated by `PYDECORATORS_REDIS_URL`. Leave that environment variable unset for normal local runs. Set it to a disposable Redis database URL when you want the integration test to exercise the real Lua script against Redis; the test uses a unique key prefix and removes matching keys afterward.

### Redis outage and fallback policy

Distributed rate limiting adds a new operational dependency: Redis must be reachable for the wrapper to decide whether a call is allowed. The decorator deliberately lets Redis client errors propagate rather than silently choosing a fallback policy for you. That is annoying in the useful way: different systems should fail differently.

Pick and document one of these policies near the call site:

**Fail closed for quota, billing, abuse, or safety boundaries.** If exceeding the limit could create financial exposure, violate a vendor contract, amplify abuse, or trigger account suspension, let the Redis error fail the operation and alert on it.

```python
@rate_limit(
    calls=100,
    period=60,
    key=lambda user_id: user_id,
    distributed=True,
    redis_url="redis://redis.example.internal:6379/0",
    redis_key_prefix="billing-api:v1",
    namespace="billable-vendor-api:v1",
)
def call_billable_vendor(user_id: str) -> str:
    ...
```

In this pattern, Redis outage is a service dependency outage. Handle it the same way you would handle the vendor being unavailable: return a controlled error, trip higher-level circuit breakers, queue work if safe, and page the owner if the dependency matters enough.

**Fail open only for best-effort convenience throttles.** If the limiter is just local politeness around non-critical work, catch Redis errors outside the decorated function and consciously bypass the distributed limiter. Do not use this for quota-protected paid APIs unless you enjoy surprise invoices, which is an eccentric hobby.

```python
def call_with_best_effort_limit(user_id: str) -> str:
    try:
        return distributed_limited_call(user_id)
    except RedisError:
        logger.warning("Redis rate limiter unavailable; bypassing best-effort limit")
        return raw_call(user_id)
```

**Use a degraded local fallback when partial protection is better than none.** For low-risk workloads, a process-local fallback can reduce blast radius during Redis outages, but it no longer coordinates across workers or hosts. Make the degraded mode visible in logs/metrics so operators know the global limit is not being enforced.

```python
@rate_limit(calls=20, period=60, key=lambda user_id: user_id)
def local_fallback_call(user_id: str) -> str:
    return raw_call(user_id)


def call_with_degraded_limit(user_id: str) -> str:
    try:
        return distributed_limited_call(user_id)
    except RedisError:
        logger.warning("Redis rate limiter unavailable; using process-local fallback")
        return local_fallback_call(user_id)
```

Use your Redis client's real exception type in production code. For `redis-py`, import it from `redis.exceptions`. Keep fallback wrappers outside `@rate_limit` so the decorator remains a predictable admission-control primitive rather than a tiny incident commander with delusions of grandeur.

## Idempotency and side effects

`@rate_limit` does not make an operation idempotent. It only controls how often the wrapped function is allowed to start in the configured process-local, same-host interprocess, or Redis-backed distributed bucket.

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
  independent containers without shared storage, or serverless instances need distributed
  mode or another external quota mechanism.
- Distributed Redis mode depends on Redis availability and correct key-prefix/namespace
  choices. A shared Redis is a coordination point, not a substitute for upstream quota
  handling, caller idempotency, or abuse controls.

## Notes

The default limiter is in-process. It is suitable for scripts, local tools, tests, and single-process services. Interprocess mode adds same-host SQLite coordination for multiple local workers. Distributed mode adds Redis-backed coordination for workers that share a Redis deployment.


## Executable examples

Copy-pasteable examples live in `docs/examples/rate_limit_examples.py` and are
covered by `tests/test_docs_examples.py`. They use an injectable clock and sleep
function so raise-mode, keyed-bucket, and block-mode behavior can be demonstrated
without real waiting.
