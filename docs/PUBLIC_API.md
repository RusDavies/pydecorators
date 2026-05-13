# Public API Policy

This project keeps its public API deliberately small.

## Public API

The public API is anything exported from `useful_decorators.__all__` and documented in the README or `docs/`.

Current public API:

- `DiskCacheBackend`
- `DiskCacheDropEvent`
- `DiskCacheMaintenanceReport`
- `CacheBackendClosedError`
- `UnsupportedCacheSchemaVersionError`
- `CacheSerializationError`
- `PickleCacheSerializer`
- `JsonCacheSerializer`
- `CacheSerializer`
- `CacheBackend`
- `MemoryCacheBackend`
- `cache_result`
- `CacheInfo`
- `CacheKeyError`
- `deprecated`
- `circuit_breaker`
- `CircuitState`
- `CircuitBreakerOpen`
- `retry`
- `rate_limit`
- `timeout`
- `log_calls`
- `measure_time`
- `TimingInfo`
- `validate_types`
- `ValidationError`
- `require_env`
- `EnvRequirementError`
- `UsefulDecoratorsError`
- `ConfigurationError`
- `RateLimitExceeded`
- `FunctionTimedOut`

## Internal API

Modules or names prefixed with `_` are internal. They may change without deprecation while the project is pre-1.0.

Examples:

- `useful_decorators._core`
- `useful_decorators._typing`

## Stability before `1.0`

Until `1.0`, public APIs may still change, but breaking changes should be:

- documented in `CHANGELOG.md`
- reflected in examples and tests
- minimized unless they fix a design mistake

## Stability after `1.0`

After `1.0`, public API changes should follow semantic versioning:

- patch releases: bug fixes only
- minor releases: backward-compatible features
- major releases: breaking changes

Deprecated APIs should generally warn for at least one minor release before removal unless keeping them would be unsafe or severely broken.

## Compatibility hardening

CI must include the minimum supported Python version from `pyproject.toml`. For the current project metadata, that means Python 3.11 must stay in the workflow matrix until support policy changes.

## Public API notes

See `docs/exceptions.md` for a centralized public exception reference.

### `UsefulDecoratorsError`

`UsefulDecoratorsError` is the base class for package-specific exceptions. Catch it when callers want to handle errors raised by this library without catching unrelated Python exceptions.

### `ConfigurationError`

`ConfigurationError` is raised when a decorator or backend receives invalid configuration, such as an unsupported async callable for `cache_result`, a non-positive TTL, or an invalid cache namespace. It inherits from `ValueError` and `UsefulDecoratorsError`.

Example: `cache_result(namespace="   ")` raises `ConfigurationError` because namespaces must not be empty.

### `CacheInfo`

`CacheInfo` is the immutable statistics object returned by planned `@cache_result` wrappers via `cache_info()`. It exposes `hits`, `misses`, `maxsize`, and `currsize`.

### `CacheKeyError`

`CacheKeyError` is raised when `@cache_result` key generation cannot produce a hashable key. It inherits from both `TypeError` and `UsefulDecoratorsError`.

Example: calling a cached function with an unhashable list argument raises `CacheKeyError` unless a custom key function converts the arguments into a hashable key.

### `MemoryCacheBackend`

`MemoryCacheBackend` is the default in-process storage backend used by `@cache_result`. It owns TTL pruning, LRU maxsize eviction, hit/miss statistics, and thread-safe cache mutation. It is public so future backend work can use the same shape as a reference implementation.

### `CacheBackend`

`CacheBackend` is the protocol implemented by cache storage backends. It defines `get`, `set_value`, `set_exception`, `clear`, and `info`. Custom backends can implement this protocol and be passed to `@cache_result(backend=...)`.

### `CacheSerializer`

`CacheSerializer` is the protocol for persistent or distributed cache payload serialization. It defines `content_type`, `dumps`, and `loads`.

### `PickleCacheSerializer`

`PickleCacheSerializer` is the default Python-object serializer intended for trusted local caches. Pickle data must not be loaded from untrusted sources.

### `JsonCacheSerializer`

`JsonCacheSerializer` serializes simple JSON-compatible values as UTF-8 `application/json` bytes for lower-risk or cross-language cache payloads. It is intended for values such as `None`, booleans, numbers, strings, lists, and dictionaries with string keys; it does not preserve arbitrary Python object types. It rejects non-finite numbers and wraps JSON serialization/deserialization failures in `CacheSerializationError`.

### `CacheSerializationError`

`CacheSerializationError` wraps serializer failures so persistent/distributed backends can expose package-specific errors instead of raw serializer internals. It inherits from `UsefulDecoratorsError`.

Example: `PickleCacheSerializer().dumps(...)` raises `CacheSerializationError` when a payload cannot be pickled.

### `CacheBackendClosedError`

`CacheBackendClosedError` is raised when a closeable cache backend such as `DiskCacheBackend` is used after `close()`. It is a package-specific `UsefulDecoratorsError`, so callers can either handle this specific lifecycle mistake or catch package errors broadly.

Example:

```python
from useful_decorators import CacheBackendClosedError, DiskCacheBackend

backend = DiskCacheBackend(".cache/example.sqlite3")
backend.close()

try:
    backend.info()
except CacheBackendClosedError:
    # Recreate the backend, skip cache use, or fix the application lifecycle.
    ...
```

For decorator-bound disk backends, prefer keeping the backend alive for the whole decorated-function lifetime and closing it from script cleanup or application shutdown.

### `UnsupportedCacheSchemaVersionError`

`UnsupportedCacheSchemaVersionError` is raised when `DiskCacheBackend` opens a SQLite cache file whose schema version is newer than this package understands. It inherits from `UsefulDecoratorsError`. Treat it as a compatibility failure: upgrade the package, point the application at a compatible cache file, or rebuild the cache.

### `DiskCacheBackend`

`DiskCacheBackend` is the SQLite-backed persistent cache backend. It implements `get`, `set_value`, `set_exception`, `clear`, `info`, and `maintain`; supports TTL expiry, LRU maxsize eviction, persistent values across backend instances, cached exceptions, explicit maintenance cleanup, context-manager cleanup, serializer content-type mismatch handling, corrupt-row dropping, and SQLite WAL/busy-timeout configuration.

### `DiskCacheMaintenanceReport`

`DiskCacheMaintenanceReport` is the immutable summary returned by `DiskCacheBackend.maintain()`. It reports `expired_rows_dropped`, `corrupt_rows_dropped`, `serializer_mismatch_rows_dropped`, and whether explicit SQLite `VACUUM` ran via `vacuumed`.

### `circuit_breaker`

`circuit_breaker` stops calling a failing sync or async dependency after a configurable failure threshold, rejects calls while open, and allows a half-open probe after the reset timeout. It supports exception-type filters, an optional exception predicate, injectable clocks for tests, and decorated-function state inspection helpers. See `docs/circuit_breaker.md` for behavior and examples.

### `CircuitState`

`CircuitState` exposes the breaker state names: `CLOSED`, `OPEN`, and `HALF_OPEN`.

### `CircuitBreakerOpen`

`CircuitBreakerOpen` is raised when a call is rejected because the circuit is open. It exposes `reset_after`.

### `retry`

`retry` retries sync and async callables after configured exception types. It is configured-only and supports explicit attempts, delay, exponential backoff, max delay, jitter, exception filtering, a `retry_if` predicate, attempt hooks, and injectable sleep functions for tests. Invalid retry policy raises `ConfigurationError` at decoration time. See `docs/retry.md` for behavior and examples.

### `rate_limit`

`rate_limit` applies in-process sliding-window limits to sync and async callables. It supports global and keyed buckets, raise or block mode, injectable clocks and sleep functions for tests, and raises `RateLimitExceeded` when a call exceeds the allowance in raise mode. See `docs/rate_limit.md` for behavior and examples.

### `log_calls`

`log_calls` logs call start, completion duration, optional argument metadata, optional summarized return values, and exceptions for sync and async callables. Argument and result logging are opt-in because logs are a common place to accidentally preserve secrets. See `docs/log_calls.md` for behavior and security notes.

### `measure_time`

`measure_time` records sync and async function duration and emits timing data through an optional callback, logger, or metrics hook. It records success and failure timings while re-raising wrapped exceptions unchanged. See `docs/measure_time.md` for behavior and examples.

### `TimingInfo`

`TimingInfo` is the immutable dataclass emitted to `measure_time(callback=...)`. It exposes `function`, `duration`, `success`, and optional `exception`.

### `validate_types`

`validate_types` performs lightweight runtime checks for annotated arguments and optionally annotated return values. It supports common built-in classes, shallow container origins by default, optional deep validation for supported container contents, `Any`, optional/union types, `Literal[...]`, and `Annotated[...]` base-type validation. Validation mismatches raise `ValidationError`, which still inherits from `TypeError` for compatibility with ordinary type-check handling. It is intentionally not a full schema-validation system. See `docs/validate_types.md` for behavior and limitations.

### `ValidationError`

`ValidationError` is raised when `@validate_types` finds an argument or return value that does not match a supported annotation. It inherits from `TypeError` and `UsefulDecoratorsError`, so callers can either treat it like ordinary Python type misuse or catch package-specific validation failures explicitly.

### `require_env`

`require_env` checks required environment variables at call time before running sync or async functions. It supports multiple required names, custom validators, and injectable environment mappings for tests. Missing or invalid variables raise `EnvRequirementError`. See `docs/require_env.md` for behavior and examples.

### `EnvRequirementError`

`EnvRequirementError` is raised when a required environment variable is missing or fails validation. It exposes `variable` and `reason` fields.

### `RateLimitExceeded`

`RateLimitExceeded` is raised when a rate-limited call exceeds its configured allowance in raise mode. It inherits from `UsefulDecoratorsError`.

### `timeout`

`timeout` applies an async deadline using `asyncio.wait_for`. It supports `seconds`, optional custom messages, and custom exception types. Synchronous functions are rejected with `ConfigurationError` until a safe sync strategy is deliberately designed. See `docs/timeout.md` for behavior and examples.

### `FunctionTimedOut`

`FunctionTimedOut` is raised when a decorated async function exceeds its configured timeout. It inherits from `TimeoutError` and `UsefulDecoratorsError`.
