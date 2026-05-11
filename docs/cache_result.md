# `@cache_result` Design

`@cache_result` caches function results in memory with predictable TTL and bounded-size behavior.

This decorator is intended for local, process-memory caching. It is not a distributed cache, not a persistence layer, and not a replacement for Redis. Tiny hammer, not industrial pile driver.

## Proposed signature

```python
from collections.abc import Callable, Hashable
from typing import Any


def cache_result(
    *,
    ttl: float | None = None,
    maxsize: int | None = 128,
    key: Callable[..., Hashable] | None = None,
    typed: bool = False,
    cache_exceptions: bool = False,
    clock: Callable[[], float] | None = None,
) -> Callable[..., Any]: ...
```

## Parameters

- `ttl`: optional lifetime in seconds for each cached entry.
  - `None` means entries do not expire by time.
  - Must be greater than zero when provided.
- `maxsize`: maximum number of entries to keep.
  - `None` means unbounded cache.
  - Must be greater than zero when provided.
  - Default: `128`.
- `key`: optional custom cache-key function.
  - Called with the same `*args, **kwargs` as the wrapped function.
  - Must return a hashable value.
- `typed`: include argument value types in the generated default key.
  - Similar spirit to `functools.lru_cache(typed=True)`.
- `cache_exceptions`: whether matching exceptions should be cached and re-raised.
  - Default: `False`.
  - If enabled, exceptions are stored as cache entries.
- `clock`: injectable monotonic clock for tests.
  - Defaults to `useful_decorators._core.monotonic`.

## Bare vs configured usage

`@cache_result` should be configured-only.

Good:

```python
@cache_result(ttl=60, maxsize=256)
def load_user(user_id: str) -> User: ...
```

Not supported:

```python
@cache_result
def load_user(user_id: str) -> User: ...
```

Reason: caching semantics should be visible at the call site. Invisible caching is where debugging goes to drink.

## Implementation strategy

Do **not** wrap or extend `functools.lru_cache` for the first implementation.

Use a small custom cache implementation instead because this decorator needs combined behavior that `lru_cache` does not expose cleanly:

- TTL expiry per entry
- injectable clock for deterministic tests
- optional custom key function
- optional exception caching
- explicit `cache_clear()` and `cache_info()` attributes
- future async support with separate handling

The implementation should use `collections.OrderedDict` or normal `dict` insertion-order behavior to support LRU-style eviction. Prefer `OrderedDict` for clarity.

## Cache entry model

Each entry should store:

- cached value or exception
- expiry timestamp, or `None`
- marker indicating whether the payload is an exception

Suggested internal shape:

```python
@dataclass(slots=True)
class CacheEntry:
    payload: object
    expires_at: float | None
    is_exception: bool = False
```

## Key generation

Default key generation should support common Python call shapes:

- positional arguments
- keyword arguments, order-insensitive
- optional typed mode

If arguments are not hashable, raise `ConfigurationError` or a dedicated cache key error at call time with a clear message.

Custom key function errors should be allowed to propagate unless a clearer package-specific error is introduced later.

## Public wrapper attributes

The wrapped function should expose:

- `cache_clear() -> None`
- `cache_info() -> CacheInfo`

Suggested `CacheInfo` shape:

```python
@dataclass(frozen=True, slots=True)
class CacheInfo:
    hits: int
    misses: int
    maxsize: int | None
    currsize: int
```

## Sync and async

First implementation should prioritize sync support.

Async support should either:

1. be implemented in the same slice with separate async locking/await handling, or
2. be explicitly deferred with docs and tests proving async functions are rejected clearly.

Recommendation: implement sync first and explicitly defer async unless the implementation stays simple.

## Thread safety

Initial implementation should be thread-safe for sync functions using `threading.RLock` around cache mutation.

The wrapped function itself should not execute while holding the lock. Lock only around cache lookups, cache updates, stats updates, and eviction.

## Error behavior

- Invalid decorator configuration raises `ConfigurationError` at decoration time.
- Unhashable generated keys raise a clear runtime exception.
- Wrapped function exceptions are not cached unless `cache_exceptions=True`.
- Cached exceptions are re-raised on cache hits.

## Metadata preservation

Use `mirror_metadata()` so `__name__`, `__doc__`, annotations, and `__wrapped__` survive decoration.
