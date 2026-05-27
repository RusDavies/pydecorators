# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow semantic versioning once public releases begin.

## [Unreleased]

## [0.1.5] - 2026-05-27

### Changed

- Bumped package metadata and runtime `__version__` for the next patch release.

## [0.1.4] - 2026-05-21

### Fixed

- Changed the PyPI-facing README release and decorator documentation references from code-styled Markdown file paths to normal human-readable outbound GitHub links, so PyPI renders them as obvious clickable documentation links.

## [0.1.3] - 2026-05-21

### Changed

- Replaced raw Markdown documentation references with absolute GitHub links so PyPI renders documentation navigation correctly.
- Added a GitHub documentation project URL for the package.
- Documented the 2026-05-21 security audit and release-readiness follow-up work.
- Added GitHub environment wait timers for TestPyPI and PyPI trusted publishing.

### Security

- Rejected Redis glob metacharacters in `RedisCacheBackend.key_prefix` before prefixes are used in Redis scan/delete/eviction patterns.
- Switched the local coverage-summary helper from `xml.etree.ElementTree` to `defusedxml.ElementTree`.

## [0.1.2] - 2026-05-20

### Changed

- Made README documentation links absolute GitHub URLs so PyPI does not turn them into project-page 404s.
- Added a dedicated PyPI project metadata documentation URL.

## [0.1.1] - 2026-05-20

### Changed

- Cleaned the PyPI-facing README now that the package is published.
- Replaced stale pre-release and dogfood-blocker wording with current install and release-gate guidance.
- Polished documentation links so readers see human-facing guide names instead of raw file paths.
- Clarified that `blakemere-wraptools` is the distribution name and `pydecorators` is the import package.

### Added

- Aggregate timestamp diagnostic guidance for future disk-cache inspection reports.
- Inspection report retention/deletion guidance for future disk-cache support artifacts.
- Inspection sensitivity-warning design guidance for future disk-cache support tooling.
- Inspection CLI safe-default design guidance for future disk-cache tooling.
- Aggregate-only disk-cache inspection report design guidance for future support bundles.
- Support-bundle metadata sensitivity guidance for no-preview disk-cache inspection reports.
- No-preview support bundle/CI guidance for future disk-cache inspection tooling.
- `preview_redactor` callback design guidance for future disk-cache inspection previews.
- Payload preview redaction guidance for future disk-cache inspection tooling.
- Bounded payload preview policy guidance for future disk-cache inspection APIs.
- Disk-cache schema metadata table design guidance for future file-compatibility promises.
- Supported cache-inspection API design guidance for future disk-cache tooling.
- SQLite column-stability guidance for disk-cache debugging versus internal implementation details.
- SQLite inspection example for JSON disk-cache rows.
- Executable datetime/bytes JSON serializer adapter recipe for disk cache payloads.
- Opt-in `coalesce_misses=True` request coalescing for duplicate concurrent cache misses.
- Request coalescing design guidance for duplicate concurrent cache misses.
- Opt-in `refresh_ttl_on_hit` sliding TTL behavior for memory and disk cache backends.
- Disk cache integrity-check and maintenance helper design guidance.
- `DiskCacheBackend(on_drop=...)` diagnostics for rows dropped because of serializer mismatches or corrupt payloads.
- `JsonCacheSerializer` for simple JSON-compatible persistent cache payloads.
- README Python code-block extraction and sync policy tests.
- Release checklist guidance for persistent disk-cache migration and clearing.
- `DiskCacheBackend` cache versioning and schema-change guidance.
- `DiskCacheBackend` namespace/key stability documentation.
- `DiskCacheBackend` persistence documentation example coverage.
- Stale ignore-pattern validation for the optional external documentation link checker.
- HTTP(S) URL-shape validation for external link ignore patterns.
- Reason-comment validation for external link ignore patterns.
- Verbose reporting for checked and ignored external documentation links.
- Ignore-file support for the optional external documentation link checker.
- Retry/backoff support for the optional external documentation link checker.
- Opt-in external documentation link checker.
- External HTTP(S) documentation link syntax policy.
- Duplicate Markdown heading anchor handling.
- Contributor guidance for documentation index inclusion.
- README core documentation link policy.
- Shared documentation policy helper module.
- Contributor checklist for documentation file updates.
- Contributor guidance for documentation policy test markers.
- Pytest marker for documentation policy checks.
- Dedicated documentation policy test module.
- Pre-release docs policy script.
- Release documentation maintenance checklist section.
- Root documentation index-linking policy documentation.
- Root docs documentation-index mention policy test.
- Root documentation local Markdown link validation.
- All-docs local Markdown link and anchor validation.
- Local Markdown anchor validation for docs index links.
- Docs index executable example conventions link policy test.
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
- Empty typed `pydecorators` package.
- Import smoke test.
- API design notes and shared internal decorator helpers.
- Public exception hierarchy.
