# API Reference

This page is the quick map of the supported surface area: decorators, cache backends,
serializers, result types, and public exceptions exported by `pydecorators`.

Use it to answer two practical questions: "What can I import?" and "Where do I go for
the behavior details?" It is intentionally compact. The reference names the public
object and its contract; the linked design pages explain the edge cases, failure modes,
and trade-offs. Nobody benefits from pretending a reference page is a novella.

For stability rules, see [Public API policy](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md). For exception inheritance and handling examples, see [Public exceptions](https://github.com/RusDavies/pydecorators/blob/master/docs/exceptions.md).

## Decorators

### `deprecated(reason=None, *, replacement=None, version=None, category=DeprecationWarning, stacklevel=2)`

Emit a deprecation warning when a sync or async function is called. Supports bare and configured usage. See [`@deprecated`](https://github.com/RusDavies/pydecorators/blob/master/docs/deprecated.md).

### `cache_result(*, ttl=None, maxsize=128, key=None, typed=False, cache_exceptions=False, refresh_ttl_on_hit=False, coalesce_misses=False, clock=None, backend=None, namespace=None)`

Cache sync function results in memory or a configured backend. Supports TTL, maxsize/LRU behavior, custom key functions, namespaces, cached exceptions, miss coalescing diagnostics via `cache_coalescing_info()`, and memory/disk backends. Async callables are rejected until async cache semantics are deliberately designed. See [`@cache_result`](https://github.com/RusDavies/pydecorators/blob/master/docs/cache_result.md).

### `cache_namespace(name, version)`

Build a conventional versioned cache namespace string such as `users:v1` for long-lived cache examples and applications.

### `retry(*, attempts, delay=0, backoff=1, max_delay=None, jitter=0, exceptions=(Exception,), retry_if=None, on_attempt=None, sleep=None, async_sleep=None)`

Retry sync or async callables after configured failures. See [`@retry`](https://github.com/RusDavies/pydecorators/blob/master/docs/retry.md).

### `rate_limit(*, calls, period, key=None, mode="raise", clock=None, sleep=None, async_sleep=None)`

Apply an in-process sliding-window rate limit to sync or async callables. See [`@rate_limit`](https://github.com/RusDavies/pydecorators/blob/master/docs/rate_limit.md).

### `timeout(*, seconds, message=None, exception_type=FunctionTimedOut)`

Apply an async timeout using `asyncio.wait_for`. Sync callables are rejected. See [`@timeout`](https://github.com/RusDavies/pydecorators/blob/master/docs/timeout.md).

### `log_calls(*, logger=None, level=logging.INFO, include_args=False, include_result=False, redact_args=(), summarize_result=None, log_exceptions=True, clock=None)`

Log start, finish duration, optional arguments, optional result summaries, and exceptions for sync or async callables. See [`@log_calls`](https://github.com/RusDavies/pydecorators/blob/master/docs/log_calls.md).

### `measure_time(*, callback=None, logger=None, level=logging.INFO, metrics_hook=None, clock=None)`

Measure sync or async function duration and emit `TimingInfo` through callbacks, logs, or metrics hooks. See [`@measure_time`](https://github.com/RusDavies/pydecorators/blob/master/docs/measure_time.md).

### `validate_types(*, validate_return=False, deep=False)`

Perform lightweight runtime checks for annotated arguments and optionally return values. `deep=True` recursively validates supported container contents. See [`@validate_types`](https://github.com/RusDavies/pydecorators/blob/master/docs/validate_types.md).

### `require_env(*names, validators=None, environ=None, messages=None, allow_empty=True)`

Require environment variables at call time before running sync or async functions. See [`@require_env`](https://github.com/RusDavies/pydecorators/blob/master/docs/require_env.md).

### `circuit_breaker(*, failure_threshold=3, reset_timeout=30.0, exceptions=(Exception,), exception_filter=None, clock=None)`

Reject calls to repeatedly failing sync or async dependencies until a reset timeout allows a half-open probe. See [`@circuit_breaker`](https://github.com/RusDavies/pydecorators/blob/master/docs/circuit_breaker.md).

## Cache APIs

### `MemoryCacheBackend(*, ttl=None, maxsize=128, refresh_ttl_on_hit=False, clock=None)`

Default in-process cache backend for `cache_result`.

### `DiskCacheBackend(path, *, ttl=None, maxsize=128, refresh_ttl_on_hit=False, serializer=None, on_drop=None, clock=None, busy_timeout_ms=5000, wal=True, drop_corrupt_rows=True)`

SQLite-backed persistent cache backend for trusted local cache files. Includes `cache_metadata()`, `inspect_integrity()`, `maintain()`, read-only `inspect_entries(...)`, and aggregate `inspect_aggregate(...)` diagnostics. See [`DiskCacheBackend`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md).

### `cache_directory(app_name, *, base_path=None)`

Return a conventional per-application cache directory path without creating directories.

### `CacheBackend`

Protocol for cache backends.

### `CacheSerializer`

Protocol for persistent/distributed cache payload serializers.

### `PickleCacheSerializer(*, protocol=pickle.HIGHEST_PROTOCOL)`

Default trusted-local serializer for disk cache payloads.

### `JsonCacheSerializer`

JSON serializer for simple JSON-compatible cache payloads.

### `RedisCacheBackend(*, client=None, url=None, key_prefix, ttl=None, serializer=None)`

Optional Redis-backed cache backend. Importing the base package does not require Redis; constructing with `url=` requires installing `blakemere-wraptools[redis]`.

The default serializer is `PickleCacheSerializer`, so Redis entries are trusted cache data. Do not use the default serializer with Redis services, key prefixes, backups, or imported payloads that untrusted users can write. Use `JsonCacheSerializer` or a reviewed custom serializer when shared Redis payloads should avoid pickle.

### `RedisCacheClient`

Small protocol for Redis-like clients accepted by `RedisCacheBackend(client=...)`.

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

### `DiskCacheIntegrityReport`

Immutable read-only integrity summary returned by `DiskCacheBackend.inspect_integrity()`.

### `DiskCacheMetadata`

Immutable cache file compatibility metadata returned by `DiskCacheBackend.cache_metadata()`.

### `DiskCachePreviewContext`

Metadata passed to `preview_redactor` callbacks during payload-preview inspection.

### `redact_json_preview(preview, context=None, *, sensitive_keys=...)`

Best-effort helper for redacting obvious sensitive JSON keys in payload previews.

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

See [Public exceptions](https://github.com/RusDavies/pydecorators/blob/master/docs/exceptions.md) for details.
