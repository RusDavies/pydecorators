# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow semantic versioning once public releases begin.

## [Unreleased]

### Added

- Docs example filename convention policy test.
- Executable docs example naming conventions.
- Docs example public-function assertion policy test.
- Docs example execution coverage policy test.
- Docs examples index coverage policy test.
- Docs index coverage policy test for top-level documentation pages.
- Docs index link validation policy test.
- Documentation index page linking core API, exception, cache, backend, and example docs.
- Centralized public exceptions reference page.
- Public exception executable examples for configuration, key, and serialization errors.
- Public exception inheritance documentation policy test.
- Public exception docs policy test.
- `CacheBackendClosedError` public docs and executable example coverage.
- `CacheBackendClosedError` README warning for context-managed decorator-bound disk backends.
- Regression coverage for decorator-bound closed `DiskCacheBackend` usage.
- `DiskCacheBackend` context-manager documentation example and executable coverage.
- Executable `DiskCacheBackend` documentation example coverage.
- `DiskCacheBackend` README lifecycle guidance showing explicit `close()` cleanup.
- `DiskCacheBackend` README usage example.
- README guidance for `DiskCacheBackend` concurrency and single-host expectations.
- `DiskCacheBackend` SQLite WAL/busy-timeout tuning options and tests.
- `DiskCacheBackend` treats corrupt disk cache payloads as misses and drops the bad row.
- Reusable cache backend conformance tests for memory and disk backend behavior.
- `DiskCacheBackend` cache operations, persistence, TTL/LRU behavior, serializer mismatch handling, and closed-backend errors.
- `DiskCacheBackend` key and payload serialization helpers.
- `DiskCacheBackend` SQLite schema initialization and constructor tests.
- `DiskCacheBackend` SQLite storage strategy design.
- `CacheSerializer` protocol and `PickleCacheSerializer` default implementation.
- `@cache_result` backend sharing semantics and `namespace=` isolation.
- `CacheBackend` protocol and `backend=` parameter for `@cache_result`.
- `MemoryCacheBackend` refactor as the default storage backend for `@cache_result`.
- `@cache_result` TTL expiry, LRU maxsize eviction, and sync mutation thread-safety coverage.
- `@cache_result` hardening tests for exception caching, lock behavior, and key canonicalization policy.
- Sync-core `@cache_result` implementation with key generation, stats, clear, and async rejection.
- `CacheInfo` and `CacheKeyError` support types for planned `@cache_result`.
- `@cache_result` API design and implementation strategy.
- Release checklist for repeatable package publishing.
- Public API policy, contributor checklist, version consistency check, and executable docs examples.
- `@deprecated` decorator with sync and async support.
- Initial project packaging foundation.
- Empty typed `useful_decorators` package.
- Import smoke test.
- API design notes and shared internal decorator helpers.
- Public exception hierarchy.
