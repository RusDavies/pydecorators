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
- [ ] Add thread-safety tests for sync cache mutation.
- [x] Decide whether async support is in-scope for `v0.1.0` or explicitly deferred.
- [x] Implement cache key generation.
- [ ] Implement TTL expiry.
- [ ] Implement max-size eviction.
- [x] Implement manual cache clear method.
- [x] Implement cache info/statistics method.
- [x] Implement sync support.
- [x] Implement async support or explicitly defer it.

### Newly Implied `@cache_result` Prep Follow-Ups

- [x] Add explicit async rejection test when `@cache_result` implementation lands.
- [x] Add public API docs entry for `CacheInfo` and `CacheKeyError`.
- [x] Add cache statistics reset behavior tests for `cache_clear()`.
- [x] Add tests for cache hits/misses.
- [ ] Add tests for TTL expiry.
- [ ] Add tests for max-size eviction.
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

- [ ] Add optional canonical key generation design note if users request call-style equivalence.
- [ ] Add race-condition policy note for duplicate concurrent misses on the same key.

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
