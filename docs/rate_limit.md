# `@rate_limit`

`@rate_limit` limits how often a sync or async function may be called. It uses a sliding-window policy so old calls expire continuously rather than only at fixed wall-clock boundaries.

```python
from useful_decorators import rate_limit


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

Invalid configuration raises `ConfigurationError` at decoration time.

## Modes

In `"raise"` mode, an exceeded call raises `RateLimitExceeded` with a retry-after hint in the message.

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

## Notes

This is an in-process rate limiter. It is suitable for scripts, local tools, tests, and single-process services. It is not a distributed quota system. Multiple processes or hosts each have their own counters unless a future shared backend is added.
