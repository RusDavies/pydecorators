# Public API Policy

This project keeps its public API deliberately small.

## Public API

The public API is anything exported from `useful_decorators.__all__` and documented in the README or `docs/`.

Current public API:

- `DiskCacheBackend`
- `CacheSerializationError`
- `PickleCacheSerializer`
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

### `CacheInfo`

`CacheInfo` is the immutable statistics object returned by planned `@cache_result` wrappers via `cache_info()`. It exposes `hits`, `misses`, `maxsize`, and `currsize`.

### `CacheKeyError`

`CacheKeyError` is raised when planned `@cache_result` key generation cannot produce a hashable key. It inherits from both `TypeError` and `UsefulDecoratorsError`.

### `MemoryCacheBackend`

`MemoryCacheBackend` is the default in-process storage backend used by `@cache_result`. It owns TTL pruning, LRU maxsize eviction, hit/miss statistics, and thread-safe cache mutation. It is public so future backend work can use the same shape as a reference implementation.

### `CacheBackend`

`CacheBackend` is the protocol implemented by cache storage backends. It defines `get`, `set_value`, `set_exception`, `clear`, and `info`. Custom backends can implement this protocol and be passed to `@cache_result(backend=...)`.

### `CacheSerializer`

`CacheSerializer` is the protocol for persistent or distributed cache payload serialization. It defines `content_type`, `dumps`, and `loads`.

### `PickleCacheSerializer`

`PickleCacheSerializer` is the default Python-object serializer intended for trusted local caches. Pickle data must not be loaded from untrusted sources.

### `CacheSerializationError`

`CacheSerializationError` wraps serializer failures so persistent/distributed backends can expose package-specific errors instead of raw serializer internals.

### `DiskCacheBackend`

`DiskCacheBackend` is the planned SQLite-backed persistent cache backend. Current implementation initializes schema; cache operations are completed in follow-up slices.
