# API Reference

This page is a compact reference for the public names exported by `useful_decorators`.

For stability rules, see [Public API policy](PUBLIC_API.md). For exception inheritance and handling examples, see [Public exceptions](exceptions.md).

## Decorators

### `deprecated(reason=None, *, replacement=None, version=None, category=DeprecationWarning, stacklevel=2)`

Emit a deprecation warning when a sync or async function is called. Supports bare and configured usage. See [`@deprecated`](deprecated.md).

### `cache_result(*, ttl=None, maxsize=128, key=None, typed=False, cache_exceptions=False, refresh_ttl_on_hit=False, coalesce_misses=False, clock=None, backend=None, namespace=None)`

Cache sync function results in memory or a configured backend. Supports TTL, maxsize/LRU behavior, custom key functions, namespaces, cached exceptions, miss coalescing diagnostics via `cache_coalescing_info()`, and memory/disk backends. Async callables are rejected until async cache semantics are deliberately designed. See [`@cache_result`](cache_result.md).

### `retry(*, attempts, delay=0, backoff=1, max_delay=None, jitter=0, exceptions=(Exception,), retry_if=None, on_attempt=None, sleep=None, async_sleep=None)`

Retry sync or async callables after configured failures. See [`@retry`](retry.md).

### `rate_limit(*, calls, period, key=None, mode="raise", clock=None, sleep=None, async_sleep=None)`

Apply an in-process sliding-window rate limit to sync or async callables. See [`@rate_limit`](rate_limit.md).

### `timeout(*, seconds, message=None, exception_type=FunctionTimedOut)`

Apply an async timeout using `asyncio.wait_for`. Sync callables are rejected. See [`@timeout`](timeout.md).

### `log_calls(*, logger=None, level=logging.INFO, include_args=False, include_result=False, redact_args=(), summarize_result=None, log_exceptions=True, clock=None)`

Log start, finish duration, optional arguments, optional result summaries, and exceptions for sync or async callables. See [`@log_calls`](log_calls.md).

### `measure_time(*, callback=None, logger=None, level=logging.INFO, metrics_hook=None, clock=None)`

Measure sync or async function duration and emit `TimingInfo` through callbacks, logs, or metrics hooks. See [`@measure_time`](measure_time.md).

### `validate_types(*, validate_return=False, deep=False)`

Perform lightweight runtime checks for annotated arguments and optionally return values. `deep=True` recursively validates supported container contents. See [`@validate_types`](validate_types.md).

### `require_env(*names, validators=None, environ=None, messages=None, allow_empty=True)`

Require environment variables at call time before running sync or async functions. See [`@require_env`](require_env.md).

### `circuit_breaker(*, failure_threshold=3, reset_timeout=30.0, exceptions=(Exception,), exception_filter=None, clock=None)`

Reject calls to repeatedly failing sync or async dependencies until a reset timeout allows a half-open probe. See [`@circuit_breaker`](circuit_breaker.md).

## Cache APIs

### `MemoryCacheBackend(*, ttl=None, maxsize=128, refresh_ttl_on_hit=False, clock=None)`

Default in-process cache backend for `cache_result`.

### `DiskCacheBackend(path, *, ttl=None, maxsize=128, refresh_ttl_on_hit=False, serializer=None, on_drop=None, clock=None, busy_timeout_ms=5000, wal=True)`

SQLite-backed persistent cache backend for trusted local cache files. Includes `maintain()`, read-only `inspect_entries(...)`, and aggregate `inspect_aggregate(...)` diagnostics. See [`DiskCacheBackend`](disk_cache_backend.md).

### `CacheBackend`

Protocol for cache backends.

### `CacheSerializer`

Protocol for persistent/distributed cache payload serializers.

### `PickleCacheSerializer(*, protocol=pickle.HIGHEST_PROTOCOL)`

Default trusted-local serializer for disk cache payloads.

### `JsonCacheSerializer`

JSON serializer for simple JSON-compatible cache payloads.

### `CacheCoalescingInfo`

Duplicate-miss coalescing diagnostics dataclass returned by `cache_coalescing_info()`.

### `CacheInfo`

Cache statistics dataclass returned by cache info helpers.

### `DiskCacheAggregateInspectionReport`

Immutable aggregate diagnostics returned by `DiskCacheBackend.inspect_aggregate()` for support-bundle-style cache summaries.

### `DiskCacheDropEvent`

Event passed to `DiskCacheBackend(on_drop=...)` when corrupt or incompatible rows are dropped.

### `DiskCacheInspectionEntry`

Immutable row-level diagnostic returned by `DiskCacheBackend.inspect_entries()`.

### `DiskCacheInspectionReport`

Immutable read-only cache inspection report returned by `DiskCacheBackend.inspect_entries()`.

### `DiskCachePreviewContext`

Metadata passed to `preview_redactor` callbacks during payload-preview inspection.

## Timing and resilience types

### `TimingInfo`

Immutable dataclass emitted by `measure_time(callback=...)` with `function`, `duration`, `success`, and optional `exception`.

### `CircuitState`

Enum with `CLOSED`, `OPEN`, and `HALF_OPEN` states.

## Exceptions

- `UsefulDecoratorsError`
- `ConfigurationError`
- `CacheKeyError`
- `ValidationError`
- `CacheSerializationError`
- `CacheBackendClosedError`
- `UnsupportedCacheSchemaVersionError`
- `RateLimitExceeded`
- `FunctionTimedOut`
- `EnvRequirementError`
- `CircuitBreakerOpen`

See [Public exceptions](exceptions.md) for details.
