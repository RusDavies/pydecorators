# TODO.md — Detailed Backlog

## 0. Project Setup

- [ ] Decide final package name and import namespace.
- [ ] Decide supported Python versions.
- [ ] Choose license.
- [ ] Create `pyproject.toml`.
- [ ] Create `src/` package layout.
- [ ] Create `tests/` layout.
- [ ] Add `README.md` with early project description.
- [ ] Add `CHANGELOG.md`.
- [ ] Add `.gitignore` for Python artifacts.
- [ ] Add formatter/linter/type-checker configuration.
- [ ] Add basic CI workflow.

## 1. API Design Backlog

- [ ] Define public decorator naming conventions.
- [ ] Decide whether decorators support both bare and configured usage.
  - Example: `@deprecated` and `@deprecated("use x instead")`.
- [ ] Define shared typing helpers using `ParamSpec` and `TypeVar`.
- [ ] Define shared sync/async detection utility.
- [ ] Define shared monotonic clock utility for testability.
- [ ] Define shared sleep utility for sync and async paths.
- [ ] Define base exceptions.
- [ ] Define configuration validation pattern.
- [ ] Ensure all decorators preserve wrapped function metadata.
- [ ] Ensure all decorators expose clear docstrings.

## 2. `@deprecated`

- [ ] Design signature.
  - [ ] `reason`
  - [ ] `replacement`
  - [ ] `version`
  - [ ] `remove_in`
  - [ ] `category`
  - [ ] `stacklevel`
- [ ] Implement sync function support.
- [ ] Implement async function support.
- [ ] Preserve function metadata.
- [ ] Emit useful warning message.
- [ ] Add tests for default warning.
- [ ] Add tests for custom message.
- [ ] Add tests for replacement/version/removal fields.
- [ ] Add async tests.
- [ ] Add README example.
- [ ] Add per-decorator docs.

## 3. `@cache_result`

- [ ] Design signature.
  - [ ] `ttl`
  - [ ] `maxsize`
  - [ ] `key`
  - [ ] `typed`
  - [ ] `cache_exceptions`
  - [ ] `clock`
- [ ] Decide whether to wrap or extend `functools.lru_cache`.
- [ ] Implement cache key generation.
- [ ] Implement TTL expiry.
- [ ] Implement max-size eviction.
- [ ] Implement manual cache clear method.
- [ ] Implement cache info/statistics method.
- [ ] Implement sync support.
- [ ] Implement async support or explicitly defer it.
- [ ] Add tests for cache hits/misses.
- [ ] Add tests for TTL expiry.
- [ ] Add tests for max-size eviction.
- [ ] Add tests for custom key function.
- [ ] Add tests for metadata preservation.
- [ ] Add README example.
- [ ] Add per-decorator docs.

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
- [ ] Add release checklist.
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
