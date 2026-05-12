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

Implemented internal shape:

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

Implemented `CacheInfo` shape:

```python
@dataclass(frozen=True, slots=True)
class CacheInfo:
    hits: int
    misses: int
    maxsize: int | None
    currsize: int
```

## Sync and async

The first implementation prioritizes sync support.

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

## Async scope decision

Async support is explicitly deferred for `v0.1.0`. The implementation rejects async callables with a clear `ConfigurationError` until async cache semantics are designed and tested separately.

Reason: caching coroutine results incorrectly is an easy way to create reused-coroutine bugs, accidental task sharing, and confusing exception behavior. Sync caching should land first; async caching deserves its own hardened slice.

## Cache key errors

Unhashable generated cache keys should raise `CacheKeyError`, which inherits from both `TypeError` and `UsefulDecoratorsError`.

## Implemented core behavior

The current implementation includes:

- sync function support
- default key generation
- custom key functions
- typed key mode
- unhashable key failures via `CacheKeyError`
- hit/miss statistics via `cache_info()`
- cache reset via `cache_clear()`
- metadata preservation
- explicit async rejection

TTL expiry and max-size LRU eviction are implemented for sync functions.

## Canonical argument binding decision

Default key generation does not canonicalize equivalent call styles in `v0.1.0`. For example, `func(1, right=2)` and `func(left=1, right=2)` are treated as different cache keys.

Reason: canonical binding requires `inspect.signature` work on every uncached call path or additional setup complexity. The first implementation keeps key generation simple and predictable. Users who need canonical behavior can provide a custom `key` function.

A future release may add opt-in canonical key generation if real usage shows it is worth the complexity. For now, this is documented as a possible future option rather than active `v0.1.0` scope.

## Lock behavior

The sync implementation protects cache lookup, mutation, statistics, and eviction with a lock, but executes the wrapped function outside that lock. This avoids blocking unrelated cache misses while a slow wrapped function runs.

## TTL and eviction behavior

TTL uses the configured monotonic clock. Entries expire when `clock() >= expires_at`. By default, TTL is fixed from write time. Set `refresh_ttl_on_hit=True` for sliding TTL behavior, where each successful hit extends that entry's expiry to `clock() + ttl`.

When `maxsize` is exceeded, the least-recently-used entry is evicted. Cache hits move entries to the most-recently-used position.

`cache_info()` prunes expired entries before reporting `currsize`.

## Duplicate concurrent misses

By default, `@cache_result` does not coalesce duplicate concurrent misses. If two threads miss the same key at the same time, both may execute the wrapped function, and the later result may overwrite the earlier cached result. This keeps lock scope small and avoids holding the cache lock while user code runs.

## Request coalescing design

`coalesce_misses=True` collapses duplicate concurrent misses for the same cache key so only the first caller computes the value and the rest wait for that in-flight computation. The option is explicit because it changes concurrency behavior and can make callers wait behind slow user code for the same key.

Implemented sync semantics:

- Coalescing is per generated cache key, after the normal `key` / `typed` / `namespace` behavior has produced a hashable key.
- The first thread that observes a miss becomes the producer for that key. It executes the wrapped function outside the backend lock.
- Later threads that miss the same key while the producer is running wait on an in-flight marker rather than executing the wrapped function again.
- Waiters must re-check the backend after the producer finishes instead of trusting a side-channel result. This keeps backend semantics authoritative for TTL, exception caching, serialization, and custom backends.
- Coalescing must not block calls for different cache keys.
- In-flight markers must be removed in a `finally` block so exceptions, cancellations via thread interruption, or unexpected errors do not permanently poison a key.

Exception behavior should follow existing cache semantics:

- If `cache_exceptions=False`, the producer raises to its caller and does not store the exception; waiters should wake, re-check the backend, see a miss, and then one waiter may become the next producer. This avoids broadcasting uncached exceptions as if they were cache entries.
- If `cache_exceptions=True`, the producer stores the exception using the backend. Waiters wake, re-check, hit the cached exception, and re-raise it through the normal cached-exception path.

Implementation sketch for the sync decorator:

- Keep a wrapper-local dictionary of in-flight keys to `threading.Condition` or `threading.Event` state.
- Protect that dictionary with its own lock, separate from backend internals.
- Do the initial backend `get()` before joining/creating an in-flight marker so ordinary hits stay fast.
- Never hold the in-flight lock while running user code or while calling backend methods that may take their own locks. Lock-order bugs are tiny deadlocks wearing clown shoes.
- After producer completion, notify all waiters, remove the marker, and let waiters perform the normal cache lookup path.

Use request coalescing when many threads may stampede the same slow cache key. Leave it disabled when duplicate work is cheap and waiting behind a slow producer would be worse than recomputing.

Non-goals for first coalescing support:

- Async request coalescing. Async caching remains a separate design.
- Cross-process coalescing for `DiskCacheBackend`. This design is process-local only.
- Fairness guarantees among many waiters.
- Cancellation/timeouts for waiting threads beyond normal Python thread behavior.
- Sharing in-flight markers across multiple wrappers that happen to share a backend. Coalescing should initially be wrapper-local; backend sharing already has enough foot-guns for one barn.

## Backend direction

The current in-process cache storage has been refactored into `MemoryCacheBackend`. The decorator still defaults to memory storage and remains backward compatible.

Future backends should follow the same separation of responsibilities: the decorator handles call wrapping and key generation; the backend handles storage, expiry, eviction, clearing, and statistics.

## Custom backend parameter

`@cache_result` accepts `backend=`. When omitted, the decorator creates a `MemoryCacheBackend` from `ttl`, `maxsize`, `refresh_ttl_on_hit`, and `clock`.

When a backend is provided, the backend owns storage policy. The decorator still owns key generation, metadata preservation, exception-caching decisions, and sync/async rejection. Backend instances are intentionally reusable, but callers should usually provide one backend per decorated function unless they deliberately want shared storage.

## Backend sharing and namespace behavior

Backend instances may be shared deliberately across decorated functions. Shared backends share storage, statistics, and clear behavior. Without a namespace, two decorated functions that produce the same generated key will read/write the same backend entry.

Use `namespace=` when sharing a backend but keeping decorated functions isolated:

```python
backend = MemoryCacheBackend()

@cache_result(backend=backend, namespace="users")
def get_user(user_id: str) -> str: ...

@cache_result(backend=backend, namespace="teams")
def get_team(team_id: str) -> str: ...
```

The namespace participates in default key generation. Custom `key` functions remain fully caller-controlled: `namespace=` is not automatically added when a custom key function is supplied. Include namespace-like separation inside the custom key function if needed.

Calling `cache_clear()` on a wrapper clears the whole backend instance. Calling `cache_info()` reports statistics for the whole backend instance. If multiple wrappers share one backend, they also share clear/statistics scope.

## Serializer interface

Persistent and distributed backends should use the `CacheSerializer` protocol rather than hard-coding a serialization format.

```python
class CacheSerializer(Protocol):
    content_type: str

    def dumps(self, value: object) -> bytes: ...
    def loads(self, data: bytes) -> object: ...
```

The default implementation is `PickleCacheSerializer`, which can round-trip ordinary Python objects for trusted caches. Pickle is unsafe for untrusted data, so disk/Redis backends must document trust boundaries clearly.

`JsonCacheSerializer` is also available for simple JSON-compatible values when payloads should be lower-risk than pickle, easier to inspect, or easier to consume from other languages. It serializes UTF-8 `application/json` bytes and intentionally does not preserve arbitrary Python object types. For common adapters such as datetimes or bytes, use an explicit custom `CacheSerializer` recipe with a distinct content type instead of relying on implicit magic.

Serializer failures should raise `CacheSerializationError`. `PickleCacheSerializer` and `JsonCacheSerializer` wrap serialization and deserialization failures in that package-specific exception.


## Backend conformance expectations

Every backend should implement the same `CacheBackend` contract before it is documented as supported. At minimum, a backend must pass the reusable conformance suite for:

- get() returning `None` for misses and `_CacheEntry` for hits
- `set_value()` replacing previous values for the same key
- `set_exception()` preserving cached exception payloads
- TTL expiry behavior and miss accounting
- max-size/LRU eviction semantics where the backend exposes `maxsize`
- `clear()` removing entries and resetting statistics
- `info()` returning `CacheInfo` with hits, misses, maxsize, and current size
- thread-safe access for the backend's documented concurrency model

Backend-specific tests are still required for storage details, serializer boundaries, operational tuning, and failure modes. The conformance suite is the floor, not the tiny decorative ceiling.

Future contributors adding a backend should first add a fixture/factory to the conformance tests, then add storage-specific tests around persistence, network or filesystem behavior, and cleanup.

## Redis backend optional-extra design

A future `RedisCacheBackend` should be an optional dependency extra, not part of the default install. Suggested packaging shape:

```toml
[project.optional-dependencies]
redis = ["redis>=5"]
```

Public import guidance should make the optional nature clear: installing `useful-decorators[redis]` enables Redis support, while the base package remains standard-library-only plus its existing local backends.

Design constraints for a first Redis backend:

- Use the same CacheBackend semantics as memory and disk backends, proven through the conformance suite.
- Use `CacheSerializer` for payloads, with a clear pickle trust-boundary warning for shared Redis deployments.
- Require an explicit namespace/prefix. Shared Redis instances make accidental key collisions too easy to leave to optimism and duct tape.
- Prefer Redis TTL primitives for expiry, while keeping `CacheInfo` honest about any statistics limitations.
- Document that Redis availability, network latency, authentication, TLS, eviction policy, and server-side persistence are operator-owned concerns.
- Do not add Redis as a hard dependency for users who only need in-process or SQLite caching.

The Redis backend should remain a design item until there is a concrete user need or release scope decision.

## Disk backend implementation

`DiskCacheBackend` implements the `CacheBackend` protocol using SQLite. It supports value and exception storage, TTL expiry, LRU maxsize eviction, persistent entries across backend instances, `clear()`, `info()`, context-manager cleanup, and package-specific `CacheBackendClosedError` failures after `close()`.

Disk payloads use the configured `CacheSerializer`; the default is `PickleCacheSerializer`, which is only safe for trusted local cache files. Use `JsonCacheSerializer` for JSON-compatible payloads when pickle is unnecessary. Rows whose stored serializer content type does not match the active serializer are treated as misses and removed rather than deserialized with the wrong serializer. `DiskCacheBackend(on_drop=...)` can report those drops, and payload deserialization failures, to logging or metrics without changing caller-facing miss behavior.

## Backend conformance tests

The test suite includes a reusable backend conformance suite that currently runs against `MemoryCacheBackend` and `DiskCacheBackend`. It checks shared `CacheBackend` behavior for hit/miss statistics, clear semantics, cached exceptions, TTL expiry, LRU eviction, and replacement of existing entries. Future backends should join this suite before being considered compatible.

Malformed disk rows are treated as misses: the disk backend deletes rows whose payload cannot be deserialized, records a miss, and lets the wrapped function recompute the value.

The disk backend requests SQLite WAL mode and a 5000 ms busy timeout by default. These settings are intended for local single-host cache ergonomics, not distributed cache semantics.

Decorator-bound disk backends should outlive calls to the decorated function. For scripts, close the backend in a `finally` block after use; for services, close it from the normal application shutdown hook.
