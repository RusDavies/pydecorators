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

- [x] Add opt-in sliding TTL refresh mode.

### Newly Implied Sliding TTL Follow-Ups

- [ ] Consider exposing refreshed expiry timestamps in disk-cache diagnostics if operators ask for TTL debugging.
- [ ] Consider documenting fixed-vs-sliding TTL tradeoffs in README if cache behavior questions recur.
- [x] Add request coalescing design for duplicate concurrent misses.

### Newly Implied Request Coalescing Follow-Ups

- [x] Implement opt-in `coalesce_misses=True` for sync `@cache_result` wrappers.
- [x] Add thread-level tests proving duplicate same-key misses coalesce while different keys continue concurrently.
- [x] Add exception-path tests for coalescing with both `cache_exceptions=False` and `cache_exceptions=True`.

### Newly Implied Request Coalescing Implementation Follow-Ups

- [ ] Consider exposing in-flight wait counters or timing diagnostics if users need visibility into coalesced waits.
- [ ] Consider adding stress tests for many waiters on one key if coalescing becomes heavily used.

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
- [x] Add JSON serializer design option for cross-language/simple-value caches.

### Newly Implied JSON Serializer Follow-Ups

- [x] Add documented serializer recipe for datetimes/bytes with JSON plus common Python scalar adapters.

### Newly Implied JSON Adapter Recipe Follow-Ups

- [ ] Consider promoting the datetime/bytes adapter recipe into a reusable helper only if multiple examples start needing the same tagged format.
- [ ] Consider adding compatibility tests for adapter tag/version changes if the recipe becomes public API rather than documentation guidance.
- [x] Add docs example that stores JSON cache rows inspected directly with SQLite.

### Newly Implied JSON Row Inspection Follow-Ups

- [ ] Consider adding a CLI-style inspection recipe if users ask for operational cache debugging workflows.
- [x] Document which SQLite columns are stable enough for debugging versus internal implementation detail before public release.

### Newly Implied SQLite Column Stability Follow-Ups

- [x] Add supported cache-inspection API design note for stable tooling beyond ad hoc SQLite debugging.

### Newly Implied Cache Inspection API Follow-Ups

- [ ] Implement `DiskCacheBackend.inspect_entries()` only if stable inspection tooling becomes part of public scope.
- [ ] Consider adding redacted key digests such as `key_sha256` if operators need to correlate rows without exposing serialized keys.
- [x] Add bounded payload preview policy design/tests before implementing any inspection API.

### Newly Implied Bounded Payload Preview Follow-Ups

- [ ] Implement payload preview helper tests only if `DiskCacheBackend.inspect_entries()` enters public scope.
- [ ] Consider making preview byte limits configurable only within a hard maximum.
- [ ] Consider documenting redaction expectations if previews may contain sensitive cached data.
- [x] Add schema-version metadata table design note before any public release that promises disk-cache file compatibility.

### Newly Implied Disk Schema Metadata Follow-Ups

- [ ] Implement `cache_metadata` only if disk-cache file compatibility becomes a public release promise.
- [ ] Add strict schema-version startup tests before implementing disk-cache migrations.
- [ ] Consider a disk-cache-specific exception for unsupported future schema versions instead of reusing `ConfigurationError`.
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

- [x] Add optional diagnostics/log hook for disk backend dropped corrupt rows.

### Newly Implied Disk Drop Diagnostics Follow-Ups

- [ ] Consider exposing structured dropped-row counters in `CacheInfo` or a disk-specific diagnostics API after user feedback.
- [ ] Consider allowing operators to opt into raising instead of dropping corrupt rows if strict cache integrity becomes useful.
- [x] Add disk backend integrity-check/maintenance helper design.

### Newly Implied Disk Maintenance Helper Follow-Ups

- [ ] Implement `DiskCacheBackend.maintain()` and `DiskCacheMaintenanceReport` if operator maintenance becomes part of the public v0.1.0 scope.
- [ ] Add tests for maintenance helper pruning expired rows, dropping corrupt payloads, reporting serializer mismatches, and explicit VACUUM behavior if implemented.
- [x] Add disk backend SQLite operational tuning decision for WAL/busy timeout.

### Newly Implied Disk SQLite Tuning Follow-Ups

- [x] Document disk backend concurrency limits and single-host expectations in README.

### Newly Implied Disk Concurrency Docs Follow-Ups

- [x] Add explicit DiskCacheBackend usage example to README.

### Newly Implied Disk README Example Follow-Ups

- [x] Add executable docs example coverage for DiskCacheBackend usage.

### Newly Implied Disk Executable Docs Follow-Ups

- [x] Add automated README code-block extraction or sync check for documented examples.

### Newly Implied README Code Block Policy Follow-Ups

- [ ] Consider executing safe README snippets once examples are factored to avoid undefined placeholders.
- [ ] Consider moving longer README snippets into docs/examples and embedding them from one source if snippet drift returns.
- [x] Add docs example coverage for DiskCacheBackend persistence across process/backend instances.

### Newly Implied Disk Persistence Docs Follow-Ups

- [ ] Add subprocess-level persistence example coverage if process-boundary behavior becomes user-facing release guidance.
- [x] Consider documenting namespace/key stability expectations more prominently for persistent cache reuse.

### Newly Implied Disk Namespace Stability Follow-Ups

- [ ] Consider adding a README note about namespace/key stability if persistent disk caching becomes a headline feature.
- [x] Consider adding cache schema/version namespace guidance before a public release.

### Newly Implied Disk Cache Versioning Follow-Ups

- [ ] Consider adding a formal cache-versioning recipe to README if persistent cache reuse becomes part of the public quickstart.
- [x] Consider adding migration/clear guidance to RELEASE.md before the first public release.

### Newly Implied Release Cache Compatibility Follow-Ups

- [ ] Consider adding a release-note template for persistent cache compatibility once public releases begin.
- [ ] Consider adding a package-level helper for recommended cache namespace/version strings if examples start repeating them.
- [x] Decide whether README examples should show explicit backend cleanup with `close()` or context-managed app lifecycle.

### Newly Implied Disk Lifecycle Docs Follow-Ups

- [x] Add context-manager DiskCacheBackend example for short scoped cache use.

### Newly Implied Disk Context-Manager Docs Follow-Ups

- [x] Add test proving decorator-bound DiskCacheBackend fails after context-manager exit.

### Newly Implied Closed Backend Regression Follow-Ups

- [x] Add a clearer README warning that context-managed disk backends are not for decorator-bound long-lived functions.
- [ ] Consider whether `cache_result` should validate closeable backends at decoration time when possible.
- [x] Document CacheBackendClosedError in README cache section.

### Newly Implied Closed Backend README Follow-Ups

- [x] Add CacheBackendClosedError to public exception examples/docs.

### Newly Implied Closed Error Public Docs Follow-Ups

- [x] Add a centralized public exceptions reference page.

### Newly Implied Public Exceptions Reference Follow-Ups

- [x] Add a docs index page linking API, exceptions, cache, disk backend, and examples.

### Newly Implied Docs Index Follow-Ups

- [x] Add policy test ensuring docs index links resolve to existing files.

### Newly Implied Docs Link Policy Follow-Ups

- [x] Add policy test that every top-level docs markdown file is linked from docs index or explicitly exempted.

### Newly Implied Docs Coverage Policy Follow-Ups

- [x] Add policy test that docs examples listed in docs index match `docs/examples/*.py`.

### Newly Implied Docs Examples Coverage Follow-Ups

- [x] Add policy test that each docs example file is executed by `tests/test_docs_examples.py` unless explicitly exempted.

### Newly Implied Docs Example Execution Follow-Ups

- [x] Refactor docs example loading into a shared helper to reduce repetitive importlib boilerplate.

### Newly Implied Docs Example Loader Refactor Follow-Ups

- [ ] Consider parameterizing docs example execution tests by module/function once the example set grows.
- [ ] Add a tiny helper for asserting expected docs example return values consistently.
- [x] Add policy test that each public example function has at least one assertion in docs example tests.

### Newly Implied Docs Example Assertion Policy Follow-Ups

- [ ] Extend docs example assertion policy if examples add public classes with public methods.
- [ ] Consider AST-based assertion detection if string matching becomes too loose.
- [x] Add a naming convention note for executable docs examples.

### Newly Implied Docs Example Naming Follow-Ups

- [x] Add policy test that executable docs example filenames follow `<topic>_examples.py` except explicit package markers.

### Newly Implied Docs Example Filename Policy Follow-Ups

- [ ] Add policy test that docs example module names match their linked labels in docs/index.md.
- [ ] Consider moving docs-example policy helpers into a dedicated test module if public API policy tests get too broad.
- [x] Add policy test that docs/index.md links to the executable example conventions section.

### Newly Implied Docs Example Conventions Link Follow-Ups

- [x] Add anchor validation for local Markdown links with `#fragment` targets.

### Newly Implied Markdown Anchor Policy Follow-Ups

- [x] Extend Markdown anchor validation to all docs Markdown links, not just docs/index.md.

### Newly Implied All-Docs Link Policy Follow-Ups

- [x] Extend local Markdown link validation to README, CONTRIBUTING, RELEASE, and other root docs.

### Newly Implied Root Docs Link Policy Follow-Ups

- [ ] Decide whether `TODO.md` should be included in root Markdown link policy long-term or exempted as mutable backlog.
- [x] Add policy test that root documentation files mention `docs/index.md` where appropriate.

### Newly Implied Root Docs Index Mention Follow-Ups

- [x] Decide whether `GOAL.md` and `PLAN.md` should link to docs/index.md or remain project-planning docs.
- [x] Consider documenting which root docs are required to link the docs index.

### Newly Implied Root Docs Policy Docs Follow-Ups

- [ ] Add policy test that planning docs stay free of release/user-doc navigation requirements unless promoted.
- [x] Consider adding a short docs-maintenance section to RELEASE.md before first release.

### Newly Implied Release Docs Maintenance Follow-Ups

- [x] Add pre-release command or script that runs only documentation policy tests.

### Newly Implied Docs Policy Command Follow-Ups

- [ ] Consider adding a package-manager alias for the docs policy script if project tooling grows beyond plain Python scripts.
- [ ] Add CI job split for documentation policy tests if CI runtime becomes noisy.
- [x] Consider splitting documentation policy tests out of `test_public_api_policy.py`.

### Newly Implied Docs Policy Test Split Follow-Ups

- [ ] Consider splitting public API exception policy tests into a dedicated exception policy module if they keep growing.
- [x] Consider adding pytest markers for documentation-policy tests.

### Newly Implied Docs Policy Marker Follow-Ups

- [ ] Consider adding a CI job that runs `pytest -m docs_policy` directly.
- [x] Add contributor guidance for when new tests should use the `docs_policy` marker.

### Newly Implied Docs Policy Marker Guidance Follow-Ups

- [x] Consider adding a short contributor checklist for updating docs policy tests when adding new docs files.

### Newly Implied Docs File Checklist Follow-Ups

- [ ] Consider adding PR-template checkboxes for docs index, docs examples, and docs policy marker updates if GitHub hosting becomes active.
- [ ] Add a docs-policy exemption registry if intentionally unindexed docs files become common.
- [x] Consider moving Markdown policy helpers into `tests/docs_policy_helpers.py` if reuse grows.

### Newly Implied Docs Policy Helpers Follow-Ups

- [x] Add unit tests for Markdown helper edge cases if link parsing grows more sophisticated.
- [ ] Consider supporting reference-style Markdown links if docs begin using them.
- [x] Decide whether external HTTP links should be syntax-checked or left unchecked.

### Newly Implied External Link Policy Follow-Ups

- [x] Consider adding an opt-in external link checker for release/manual maintenance, separate from default CI.

### Newly Implied External Link Checker Follow-Ups

- [x] Consider adding retry/backoff support to the manual external link checker if release checks see transient failures.

### Newly Implied External Link Checker Retry Follow-Ups

- [ ] Consider reporting per-attempt retry details in verbose mode if manual release checks become hard to diagnose.
- [ ] Consider capping maximum retry backoff if higher retry counts are introduced.
- [x] Add external link checker allowlist/ignore file if intentionally unstable third-party URLs appear.

### Newly Implied External Link Ignore Follow-Ups

- [x] Consider requiring comments/reasons for non-comment patterns in `.external-links-ignore` if the ignore list grows.

### Newly Implied External Link Ignore Reason Follow-Ups

- [x] Consider validating `.external-links-ignore` patterns have HTTP(S) URL shape if real ignores are added.

### Newly Implied External Link Ignore Pattern Follow-Ups

- [x] Consider validating that external link ignore patterns match at least one current docs link if the ignore file gets real entries.

### Newly Implied External Link Stale Ignore Follow-Ups

- [ ] Consider adding an explicit `--allow-stale-ignores` escape hatch if release maintenance ever needs to stage ignore entries before docs changes.
- [ ] Consider showing the matching docs link for each ignore pattern in verbose mode if the ignore file grows.
- [ ] Consider documenting wildcard semantics for `.external-links-ignore` in a dedicated maintenance doc if the checker grows further.
- [ ] Consider adding expiration dates for ignored external links if the ignore list grows.
- [x] Consider reporting ignored external links in verbose mode during release checks.

### Newly Implied External Link Verbose Follow-Ups

- [ ] Consider reporting successful checked links only in verbose mode once the checker scans more external links.
- [ ] Consider adding quiet JSON output if release automation starts consuming external link checker results.
- [ ] Add allowlist or scheme policy if docs start using non-HTTP external links intentionally.
- [x] Add duplicate-heading anchor collision handling if docs pages grow repeated headings.

### Newly Implied Duplicate Anchor Handling Follow-Ups

- [ ] Consider documenting Markdown anchor compatibility assumptions if linking rules become user-facing.
- [ ] Add helper coverage for non-ASCII headings if docs start using them.
- [x] Consider centralizing Markdown link parsing helpers for docs policy tests.
- [x] Add docs contribution note explaining when a docs page should be added to the index.

### Newly Implied Docs Index Guidance Follow-Ups

- [ ] Consider adding a docs-index section classifier policy if `docs/index.md` grows more categories.
- [ ] Add an explicit docs-index exemption list if intentional unindexed docs appear.
- [x] Add policy test checking docs links outside docs/index.md.
- [x] Add release checklist item to update docs index when adding docs pages.
- [x] Add policy test ensuring README links to core docs pages.

### Newly Implied README Core Docs Policy Follow-Ups

- [ ] Consider documenting the README core-doc link set in CONTRIBUTING if the required list grows.
- [ ] Consider grouping README documentation links into a dedicated Documentation section if the homepage grows longer.
- [x] Add tests that all public exceptions appear in public API docs.

### Newly Implied Public Exception Policy Follow-Ups

- [x] Add tests that public exception inheritance matches documented behavior.

### Newly Implied Public Exception Inheritance Follow-Ups

- [x] Add a structured public exception metadata table to docs.
- [x] Add doctested exception handling examples for public exception types.
- [x] Add short examples for `ConfigurationError`, `CacheKeyError`, and `CacheSerializationError`.

### Newly Implied Public Exception Examples Follow-Ups

- [ ] Add public exception examples for reserved future decorators once implemented.
- [x] Add README link to public exception docs once centralized exception reference exists.
- [ ] Add lifecycle guidance to disk backend design docs for service shutdown hooks.
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
