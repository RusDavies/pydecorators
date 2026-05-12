# Public API Policy

This project keeps its public API deliberately small.

## Public API

The public API is anything exported from `useful_decorators.__all__` and documented in the README or `docs/`.

Current public API:

- `DiskCacheBackend`
- `DiskCacheDropEvent`
- `CacheBackendClosedError`
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

### `DiskCacheBackend`

`DiskCacheBackend` is the SQLite-backed persistent cache backend. It implements `get`, `set_value`, `set_exception`, `clear`, and `info`; supports TTL expiry, LRU maxsize eviction, persistent values across backend instances, cached exceptions, context-manager cleanup, serializer content-type mismatch handling, corrupt-row dropping, and SQLite WAL/busy-timeout configuration.

### `RateLimitExceeded`

`RateLimitExceeded` is reserved for rate-limiting decorators and is raised when a rate-limited call exceeds its configured allowance. It inherits from `UsefulDecoratorsError`.

### `FunctionTimedOut`

`FunctionTimedOut` is reserved for timeout decorators and is raised when a decorated function exceeds its configured timeout. It inherits from `TimeoutError` and `UsefulDecoratorsError`.
