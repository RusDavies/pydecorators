# TODO.md — Detailed Backlog

## 0. Project Setup

- [x] Decide final package name and import namespace.
- [x] Decide supported Python versions.
- [x] Choose license.
- [x] Create `pyproject.toml`.
- [x] Create `src/` package layout.
- [x] Create `tests/` layout.
- [x] Add `README.md` with early project description.
- [x] Add `CHANGELOG.md`.
- [x] Add `.gitignore` for Python artifacts.
- [x] Add formatter/linter/type-checker configuration.
- [x] Add basic CI workflow.

## 1. API Design Backlog

- [x] Define public decorator naming conventions.
- [x] Decide whether decorators support both bare and configured usage.
  - Example: `@deprecated` and `@deprecated("use x instead")`.
- [x] Define shared typing helpers using `ParamSpec` and `TypeVar`.
- [x] Define shared sync/async detection utility.
- [x] Define shared monotonic clock utility for testability.
- [x] Define shared sleep utility for sync and async paths.
- [x] Define base exceptions.
- [x] Define configuration validation pattern.
- [x] Ensure all decorators preserve wrapped function metadata.
- [x] Ensure all decorators expose clear docstrings.

### Newly Implied API Design Follow-Ups

- [x] Add tests that every public decorator is listed in `__all__`.
- [x] Add documentation policy for what counts as public API.
- [x] Add version consistency check between `pyproject.toml` and `useful_decorators.__version__`.
- [x] Decide whether internal helpers should use protocols for callable clock/sleep injection.
- [x] Add contributor guidance for adding a new decorator end-to-end.

## 2. `@deprecated`

- [x] Design signature.
  - [x] `reason`
  - [x] `replacement`
  - [x] `version`
  - [x] `remove_in`
  - [x] `category`
  - [x] `stacklevel`
- [x] Implement sync function support.
- [x] Implement async function support.
- [x] Preserve function metadata.
- [x] Emit useful warning message.
- [x] Add tests for default warning.
- [x] Add tests for custom message.
- [x] Add tests for replacement/version/removal fields.
- [x] Add async tests.
- [x] Add README example.
- [x] Add per-decorator docs.

### Newly Implied `@deprecated` Follow-Ups

- [x] Add stacklevel behavior tests that verify warnings point at caller code.
- [x] Add class/method deprecation examples.
- [x] Decide whether deprecating classes should be supported explicitly.
- [x] Add documentation for warning filters and why `DeprecationWarning` may be hidden by default.
- [x] Add type-checking examples for decorators used bare and configured.

### Newly Implied Documentation Follow-Ups

- [x] Add executable documentation examples or doctest-style validation.
- [x] Add a public API stability policy before first release.

### Newly Implied Hardening Follow-Ups

- [x] Add automated validation that documented public API names match `__all__`.
- [x] Add CI matrix coverage for the minimum supported Python version locally or via CI artifact review.

### Newly Implied Release Hardening Follow-Ups

- [x] Add a dedicated release checklist file before publishing `v0.1.0`.

## 3. `@cache_result`

- [x] Design signature.
  - [x] `ttl`
  - [x] `maxsize`
  - [x] `key`
  - [x] `typed`
  - [x] `cache_exceptions`
  - [x] `clock`
- [x] Decide whether to wrap or extend `functools.lru_cache`.

### Newly Implied `@cache_result` Design Follow-Ups

- [x] Define `CacheInfo` public shape.
- [x] Define internal `CacheEntry` shape.
- [x] Decide exact runtime exception type for unhashable cache keys.
- [x] Add thread-safety tests for sync cache mutation.
- [x] Decide whether async support is in-scope for `v0.1.0` or explicitly deferred.
- [x] Implement cache key generation.
- [x] Implement TTL expiry.
- [x] Implement max-size eviction.
- [x] Implement manual cache clear method.
- [x] Implement cache info/statistics method.
- [x] Implement sync support.
- [x] Implement async support or explicitly defer it.

### Newly Implied `@cache_result` Prep Follow-Ups

- [x] Add explicit async rejection test when `@cache_result` implementation lands.
- [x] Add public API docs entry for `CacheInfo` and `CacheKeyError`.
- [x] Add cache statistics reset behavior tests for `cache_clear()`.
- [x] Add tests for cache hits/misses.
- [x] Add tests for TTL expiry.
- [x] Add tests for max-size eviction.

### Newly Implied `@cache_result` Policy Follow-Ups

- [x] Add tests for TTL behavior with cached exceptions.
- [x] Add docs note that `cache_info()` prunes expired entries before reporting `currsize`.
- [x] Decide whether TTL should refresh on cache hit in a future sliding-expiration mode.
- [x] Add tests for custom key function.
- [x] Add tests for metadata preservation.
- [x] Add README example.
- [x] Add per-decorator docs.
### Newly Implied `@cache_result` Sync-Core Follow-Ups

- [x] Add tests for `cache_exceptions=True`.
- [x] Add tests proving wrapped function execution happens outside the cache lock.
- [x] Add tests for positional-vs-keyword equivalent calls if canonical argument binding is desired.
- [x] Decide whether default key generation should canonicalize calls using `inspect.signature`.

### Newly Implied `@cache_result` Hardening Follow-Ups

- [x] Add optional canonical key generation design note if users request call-style equivalence.
- [x] Add race-condition policy note for duplicate concurrent misses on the same key.

### Newly Implied `@cache_result` Future Options

- [ ] Consider opt-in sliding TTL refresh mode after user feedback.
- [ ] Consider request coalescing for duplicate concurrent misses after user feedback.

### Newly Implied `@cache_result` Backend Follow-Ups

- [x] Refactor current in-memory cache storage into `MemoryCacheBackend`.
- [x] Define a formal cache backend protocol/interface.
- [x] Add `backend=` parameter to `@cache_result` while preserving memory default.

### Newly Implied Backend Interface Follow-Ups

- [x] Document whether backend instances should be shared across decorated functions.
- [x] Add tests for deliberately shared backend instances across multiple decorated functions.
- [x] Decide whether backend implementations should receive namespace/prefix support.

### Newly Implied Backend Semantics Follow-Ups

- [x] Decide whether custom `key` functions should receive namespace automatically or remain fully caller-controlled.
- [x] Add docs warning that sharing a backend also shares `cache_clear()` and `cache_info()` scope.

### Newly Implied Backend Namespace Follow-Ups

- [x] Add test showing custom `key` functions remain responsible for namespace separation.
- [x] Decide serializer interface for persistent/distributed backends.

### Newly Implied Serializer Follow-Ups

- [x] Decide whether serializer failures need a package-specific exception type.
- [ ] Add JSON serializer design option for cross-language/simple-value caches.
- [x] Document pickle trust-boundary warning in disk/Redis backend docs.
- [x] Design `DiskCacheBackend` storage strategy, likely SQLite.

### Newly Implied Disk Backend Follow-Ups

- [x] Implement `DiskCacheBackend` SQLite schema initialization.

### Newly Implied Disk Schema Follow-Ups

- [x] Decide whether `DiskCacheBackend.close()` should make later operations raise a package-specific error.
- [x] Add context-manager support for `DiskCacheBackend`.
- [x] Implement disk backend key serialization helpers.
- [x] Implement disk backend payload serialization helpers.

### Newly Implied Disk Serialization Follow-Ups

- [x] Add disk backend serializer content-type mismatch handling.
- [x] Add tests for custom disk backend serializer.
- [x] Implement disk backend `get`, `set_value`, `set_exception`, `clear`, and `info`.
- [x] Add disk backend persistence tests across backend instances.
- [x] Add disk backend SQLite trust-boundary warning to README.

### Newly Implied Disk Operations Follow-Ups

- [x] Add disk backend corrupt-row handling policy and tests.

### Newly Implied Disk Corrupt-Row Follow-Ups

- [ ] Add optional diagnostics/log hook for disk backend dropped corrupt rows.
- [ ] Add disk backend integrity-check/maintenance helper design.
- [x] Add disk backend SQLite operational tuning decision for WAL/busy timeout.

### Newly Implied Disk SQLite Tuning Follow-Ups

- [x] Document disk backend concurrency limits and single-host expectations in README.

### Newly Implied Disk Concurrency Docs Follow-Ups

- [x] Add explicit DiskCacheBackend usage example to README.

### Newly Implied Disk README Example Follow-Ups

- [x] Add executable docs example coverage for DiskCacheBackend usage.

### Newly Implied Disk Executable Docs Follow-Ups

- [ ] Add automated README code-block extraction or sync check for documented examples.
- [ ] Add docs example coverage for DiskCacheBackend persistence across process/backend instances.
- [x] Decide whether README examples should show explicit backend cleanup with `close()` or context-managed app lifecycle.

### Newly Implied Disk Lifecycle Docs Follow-Ups

- [x] Add context-manager DiskCacheBackend example for short scoped cache use.

### Newly Implied Disk Context-Manager Docs Follow-Ups

- [x] Add test proving decorator-bound DiskCacheBackend fails after context-manager exit.

### Newly Implied Closed Backend Regression Follow-Ups

- [ ] Add a clearer README warning that context-managed disk backends are not for decorator-bound long-lived functions.
- [ ] Consider whether `cache_result` should validate closeable backends at decoration time when possible.
- [ ] Document CacheBackendClosedError in README cache section.
- [x] Add note that decorator-bound disk backends should outlive decorated function use.
- [ ] Document recommended cache file location/permissions for CLI and service use.
- [ ] Add stress/smoke test for concurrent disk backend reads and writes.
- [ ] Decide whether disk backend should expose cache vacuum/compaction maintenance.
- [x] Add reusable backend conformance tests for cached exception behavior, TTL, LRU, clear, and stats.
- [ ] Design `RedisCacheBackend` as optional dependency extra.
- [x] Add backend conformance test suite reusable by memory/disk/redis backends.

### Newly Implied Backend Conformance Follow-Ups

- [ ] Document backend conformance expectations for future backend contributors.
- [ ] Add Redis backend to conformance suite when Redis backend exists.
- [ ] Reduce duplicate backend behavior tests now covered by the conformance suite.

## 4. `@retry`

- [ ] Design signature.
  - [ ] `attempts`
  - [ ] `delay`
  - [ ] `backoff`
  - [ ] `max_delay`
  - [ ] `jitter`
  - [ ] `exceptions`
  - [ ] `retry_if`
  - [ ] `before_attempt`
  - [ ] `after_attempt`
  - [ ] `sleep`
- [ ] Implement configuration validation.
- [ ] Implement sync retry loop.
- [ ] Implement async retry loop.
- [ ] Implement exponential backoff.
- [ ] Implement jitter.
- [ ] Implement exception filtering.
- [ ] Implement predicate-based retry decision.
- [ ] Add tests for success after retry.
- [ ] Add tests for exhausted attempts.
- [ ] Add tests for non-retryable exceptions.
- [ ] Add tests for backoff calculation.
- [ ] Add tests using fake sleep to avoid slow tests.
- [ ] Add async tests.
- [ ] Add README example.
- [ ] Add per-decorator docs.

## 5. `@rate_limit`

- [ ] Design signature.
  - [ ] `calls`
  - [ ] `period`
  - [ ] `key`
  - [ ] `mode`: raise or block
  - [ ] `clock`
  - [ ] `sleep`
- [ ] Decide token bucket vs sliding window implementation.
- [ ] Implement global rate limit.
- [ ] Implement key-based rate limit.
- [ ] Implement raise mode.
- [ ] Implement blocking mode.
- [ ] Implement async support.
- [ ] Define `RateLimitExceeded` exception.
- [ ] Add tests for allowed calls.
- [ ] Add tests for exceeded calls.
- [ ] Add tests for window reset.
- [ ] Add tests for key-based isolation.
- [ ] Add tests with fake clock/sleep.
- [ ] Add README example.
- [ ] Add per-decorator docs.

## 6. `@timeout`

- [ ] Design signature.
  - [ ] `seconds`
  - [ ] `message`
  - [ ] `exception`
- [ ] Define timeout exception.
- [ ] Implement async timeout using `asyncio.wait_for`.
- [ ] Evaluate sync timeout strategies.
  - [ ] Signal-based Unix timeout.
  - [ ] Thread-based timeout with documented limitations.
  - [ ] Explicitly async-only for first release.
- [ ] Choose conservative sync behavior.
- [ ] Add tests for async timeout success.
- [ ] Add tests for async timeout failure.
- [ ] Add tests for metadata preservation.
- [ ] Add docs warning about sync limitations.
- [ ] Add README example.

## 7. Observability Decorators Backlog

### `@log_calls`

- [ ] Design signature.
- [ ] Add argument redaction support.
- [ ] Add return value redaction/summarization.
- [ ] Add exception logging.
- [ ] Add duration logging.
- [ ] Add sync tests.
- [ ] Add async tests.
- [ ] Add security docs.

### `@measure_time`

- [ ] Design signature.
- [ ] Add callback support.
- [ ] Add logger support.
- [ ] Add metrics hook support.
- [ ] Add sync tests.
- [ ] Add async tests.
- [ ] Add examples.

## 8. Validation and Configuration Decorators Backlog

### `@validate_types`

- [ ] Decide whether to use standard-library type inspection only.
- [ ] Support basic built-in types.
- [ ] Support `Optional`/union types.
- [ ] Support return value validation option.
- [ ] Add clear validation error messages.
- [ ] Add tests.
- [ ] Document limitations.

### `@require_env`

- [ ] Design signature.
- [ ] Support required variable names.
- [ ] Support custom validators.
- [ ] Support loading only at call time.
- [ ] Add tests with patched environment.
- [ ] Add CLI/script examples.

## 9. Resilience Decorators Backlog

### `@circuit_breaker`

- [ ] Design signature.
- [ ] Define states: closed, open, half-open.
- [ ] Track failure counts.
- [ ] Track reset timeout.
- [ ] Support exception filters.
- [ ] Add sync support.
- [ ] Add async support.
- [ ] Add tests with fake clock.
- [ ] Add docs with service-client examples.

## 10. Documentation Backlog

- [ ] Write README quick start.
- [ ] Add installation instructions.
- [ ] Add one example per first-release decorator.
- [ ] Add decorator comparison table or bullet list.
- [ ] Add security notes.
- [ ] Add async usage notes.
- [ ] Add timeout limitations note.
- [ ] Add contributing guide.
- [ ] Add release process notes.
- [ ] Add API reference documentation.

## 11. Quality Backlog

- [ ] Add unit test coverage target.
- [ ] Add coverage reporting.
- [ ] Add type checking gate.
- [ ] Add linting gate.
- [ ] Add formatting gate.
- [ ] Add packaging build check.
- [ ] Add import smoke test.
- [ ] Add examples smoke test.
- [ ] Add pre-commit configuration if useful.

## 12. Release Backlog

- [ ] Confirm PyPI package name availability.
- [ ] Add package metadata.
- [ ] Add project URLs.
- [ ] Add classifiers.
- [ ] Add license file.
- [ ] Add versioning strategy.
- [x] Add release checklist.

### Newly Implied Release Checklist Follow-Ups

- [ ] Add clean-venv local wheel install smoke test script.
- [ ] Add TestPyPI/PyPI publishing instructions once package credentials and repository location are finalized.
- [ ] Add git tag naming convention for releases.
- [ ] Build package locally.
- [ ] Test install from local wheel.
- [ ] Publish test release to TestPyPI.
- [ ] Publish `v0.1.0` to PyPI when ready.

## 13. Future Ideas

- [ ] Optional Redis-backed cache.
- [ ] Optional OpenTelemetry integration.
- [ ] Optional Prometheus metrics integration.
- [ ] Optional structlog integration.
- [ ] Django/FastAPI examples.
- [ ] CLI examples.
- [ ] Benchmark suite.
- [ ] Documentation site.
