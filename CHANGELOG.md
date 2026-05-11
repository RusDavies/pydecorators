# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow semantic versioning once public releases begin.

## [Unreleased]

### Added

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
