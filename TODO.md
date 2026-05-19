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

- [x] Expose refreshed expiry timestamps in disk-cache diagnostics for TTL debugging.
- [x] Consider documenting fixed-vs-sliding TTL tradeoffs in README if cache behavior questions recur.
- [x] Add request coalescing design for duplicate concurrent misses.

### Newly Implied Request Coalescing Follow-Ups

- [x] Implement opt-in `coalesce_misses=True` for sync `@cache_result` wrappers.
- [x] Add thread-level tests proving duplicate same-key misses coalesce while different keys continue concurrently.
- [x] Add exception-path tests for coalescing with both `cache_exceptions=False` and `cache_exceptions=True`.

### Newly Implied Request Coalescing Implementation Follow-Ups

- [x] Expose in-flight wait counters and timing diagnostics via `cache_coalescing_info()`.
- [x] Add stress tests for many waiters on one coalesced cache key.

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

- [x] Decide not to promote the datetime/bytes adapter recipe into reusable public API until repeated need appears.
- [x] Decide compatibility tests for adapter tag/version changes are unnecessary while the adapter remains documentation guidance.
- [x] Add docs example that stores JSON cache rows inspected directly with SQLite.

### Newly Implied JSON Row Inspection Follow-Ups

- [x] Add a CLI-style inspection recipe for operational cache debugging workflows.
- [x] Document which SQLite columns are stable enough for debugging versus internal implementation detail before public release.

### Newly Implied SQLite Column Stability Follow-Ups

- [x] Add supported cache-inspection API design note for stable tooling beyond ad hoc SQLite debugging.

### Newly Implied Cache Inspection API Follow-Ups

- [x] Implement `DiskCacheBackend.inspect_entries()` for stable read-only diagnostics.
- [x] Add redacted `key_sha256` digests for correlating rows without exposing serialized keys.
- [x] Add bounded payload preview policy design/tests before implementing any inspection API.

### Newly Implied Bounded Payload Preview Follow-Ups

- [x] Add payload preview helper tests for `DiskCacheBackend.inspect_entries()`.
- [x] Make preview byte limits configurable within a hard maximum.
- [x] Document redaction expectations for payload previews that may contain sensitive cached data.

### Newly Implied Payload Preview Redaction Follow-Ups

- [x] Design a `preview_redactor` callback before implementing payload previews.

### Newly Implied Preview Redactor Callback Follow-Ups

- [x] Add `DiskCachePreviewContext` for inspection preview redactors.
- [x] Track redaction failure counts in `DiskCacheInspectionReport`.
- [x] Document preview redaction order and avoid built-in redaction policy for now.
- [x] Document no-previews mode for support bundles and CI artifacts if inspection tooling is added.

### Newly Implied No-Preview Safe Mode Follow-Ups

- [x] Document future inspection CLI defaulting to aggregate/no-preview safe mode.

### Newly Implied Inspection CLI Safe Default Follow-Ups

- [x] Add CLI-style help-text coverage for disk-cache inspection examples.
- [x] Add JSON-output safe-default tests for machine-readable inspection output.
- [x] Add explicit warning-channel policy before adding quiet/scripted inspection modes.
- [x] Add tests that safe mode never invokes preview redactors.
- [x] Document support-bundle metadata sensitivity even when previews are disabled.

### Newly Implied Support Bundle Metadata Follow-Ups

- [x] Add aggregate-only inspection report design before adding any support-bundle command.

### Newly Implied Aggregate Inspection Follow-Ups

- [x] Implement `DiskCacheAggregateInspectionReport` and `inspect_aggregate()` for support-bundle-style summaries.
- [x] Add aggregate truncation tests for bounded inspection scans.
- [x] Document aggregate timestamp ranges as diagnostics rather than audit evidence.

### Newly Implied Aggregate Timestamp Follow-Ups

- [x] Document aggregate timestamp/report-time fields as diagnostics, not audit evidence.
- [x] Omit per-row timestamp ranges from aggregate support-bundle reports.
- [x] Add sensitivity-warning design/tests for future inspection CLI support bundles.

### Newly Implied Inspection Warning Follow-Ups

- [x] Add `sensitivity_warning` to `DiskCacheInspectionReport`.
- [x] Add tests that preview-enabled inspection output uses stronger warnings than aggregate-only output.
- [x] Document approved quiet-mode warning channels before adding scripted inspection output.
- [x] Add retention/deletion guidance for generated cache inspection reports if support tooling is added.

### Newly Implied Inspection Report Retention Follow-Ups

- [x] Add creation-time and mode metadata to `DiskCacheInspectionReport`.
- [x] Document that future CI examples must not upload inspection reports by default.
- [x] Document short retention defaults for generated inspection reports.
- [x] Add built-in obvious JSON key redaction as defense-in-depth, not a safety guarantee.
- [x] Add schema-version metadata table design note before any public release that promises disk-cache file compatibility.

### Newly Implied Disk Schema Metadata Follow-Ups

- [x] Implement `cache_metadata` for disk-cache file compatibility diagnostics.
- [x] Add strict schema-version startup tests before implementing disk-cache migrations.
- [x] Add disk-cache-specific exception for unsupported future schema versions instead of reusing `ConfigurationError`.
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

- [x] Expose structured dropped-row counters through disk-specific `inspect_integrity()` diagnostics.
- [x] Allow operators to opt into raising instead of dropping corrupt rows with `drop_corrupt_rows=False`.
- [x] Add disk backend integrity-check/maintenance helper design.

### Newly Implied Disk Maintenance Helper Follow-Ups

- [x] Implement `DiskCacheBackend.maintain()` and `DiskCacheMaintenanceReport` if operator maintenance becomes part of the public v0.1.0 scope.
- [x] Add tests for maintenance helper pruning expired rows, dropping corrupt payloads, reporting serializer mismatches, and explicit VACUUM behavior if implemented.
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

- [x] Execute safe README snippets through `docs/examples/readme_examples.py` to avoid undefined placeholders.
- [x] Move longer README snippets into executable docs examples for drift-resistant coverage.
- [x] Add docs example coverage for DiskCacheBackend persistence across process/backend instances.

### Newly Implied Disk Persistence Docs Follow-Ups

- [x] Add subprocess-level persistence example coverage if process-boundary behavior becomes user-facing release guidance.
- [x] Consider documenting namespace/key stability expectations more prominently for persistent cache reuse.

### Newly Implied Disk Namespace Stability Follow-Ups

- [x] Consider adding a README note about namespace/key stability if persistent disk caching becomes a headline feature.
- [x] Consider adding cache schema/version namespace guidance before a public release.

### Newly Implied Disk Cache Versioning Follow-Ups

- [x] Consider adding a formal cache-versioning recipe to README if persistent cache reuse becomes part of the public quickstart.
- [x] Consider adding migration/clear guidance to RELEASE.md before the first public release.

### Newly Implied Release Cache Compatibility Follow-Ups

- [x] Consider adding a release-note template for persistent cache compatibility once public releases begin.
- [x] Add `cache_namespace()` package-level helper for recommended cache namespace/version strings.
- [x] Decide whether README examples should show explicit backend cleanup with `close()` or context-managed app lifecycle.

### Newly Implied Disk Lifecycle Docs Follow-Ups

- [x] Add context-manager DiskCacheBackend example for short scoped cache use.

### Newly Implied Disk Context-Manager Docs Follow-Ups

- [x] Add test proving decorator-bound DiskCacheBackend fails after context-manager exit.

### Newly Implied Closed Backend Regression Follow-Ups

- [x] Add a clearer README warning that context-managed disk backends are not for decorator-bound long-lived functions.
- [x] Validate provided cache backends at configuration time by calling `info()` so closed backends fail early.
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

- [x] Parameterize docs example execution tests by module/function.
- [x] Add a tiny helper for asserting expected docs example return values consistently.
- [x] Add policy test that each public example function has at least one assertion in docs example tests.

### Newly Implied Docs Example Assertion Policy Follow-Ups

- [x] Extend docs example assertion policy to cover public classes with public methods.
- [x] Consider AST-based assertion detection if string matching becomes too loose.
- [x] Add a naming convention note for executable docs examples.

### Newly Implied Docs Example Naming Follow-Ups

- [x] Add policy test that executable docs example filenames follow `<topic>_examples.py` except explicit package markers.

### Newly Implied Docs Example Filename Policy Follow-Ups

- [x] Add policy test that docs example module names match their linked labels in docs/index.md.
- [x] Generate/check the executable example list in docs/index.md.
- [x] Consider moving docs-example policy helpers into a dedicated test module if public API policy tests get too broad.
- [x] Add policy test that docs/index.md links to the executable example conventions section.

### Newly Implied Docs Example Conventions Link Follow-Ups

- [x] Add anchor validation for local Markdown links with `#fragment` targets.

### Newly Implied Markdown Anchor Policy Follow-Ups

- [x] Extend Markdown anchor validation to all docs Markdown links, not just docs/index.md.

### Newly Implied All-Docs Link Policy Follow-Ups

- [x] Extend local Markdown link validation to README, CONTRIBUTING, RELEASE, and other root docs.

### Newly Implied Root Docs Link Policy Follow-Ups

- [x] Decide whether `TODO.md` should be included in root Markdown link policy long-term or exempted as mutable backlog.
- [x] Add policy test that root documentation files mention `docs/index.md` where appropriate.

### Newly Implied Root Docs Index Mention Follow-Ups

- [x] Decide whether `GOAL.md` and `PLAN.md` should link to docs/index.md or remain project-planning docs.
- [x] Consider documenting which root docs are required to link the docs index.

### Newly Implied Root Docs Policy Docs Follow-Ups

- [x] Add policy test that planning docs stay free of release/user-doc navigation requirements unless promoted.
- [x] Consider adding a short docs-maintenance section to RELEASE.md before first release.

### Newly Implied Release Docs Maintenance Follow-Ups

- [x] Add pre-release command or script that runs only documentation policy tests.

### Newly Implied Docs Policy Command Follow-Ups

- [x] Add Hatch full-gate alias for repeated release-prep verification.
- [x] Revisit planning-doc navigation policy and keep TODO/PLAN out of public docs navigation unless they become website pages.
- [x] Add a package-manager alias for the docs policy script.
- [x] Add CI job split for documentation policy tests.
- [x] Decide to keep docs-policy in normal CI rather than path-filtering it prematurely.
- [x] Consider splitting documentation policy tests out of `test_public_api_policy.py`.

### Newly Implied Docs Policy Test Split Follow-Ups

- [x] Consider splitting public API exception policy tests into a dedicated exception policy module if they keep growing.
- [x] Consider adding pytest markers for documentation-policy tests.

### Newly Implied Docs Policy Marker Follow-Ups

- [x] Add CI job that runs `pytest -m docs_policy` directly.
- [x] Add contributor guidance for when new tests should use the `docs_policy` marker.

### Newly Implied Docs Policy Marker Guidance Follow-Ups

- [x] Consider adding a short contributor checklist for updating docs policy tests when adding new docs files.

### Newly Implied Docs File Checklist Follow-Ups

- [x] Add PR-template checkboxes for docs index, docs examples, and docs policy marker updates.
- [x] Add issue templates if external contributors start filing repeated docs/release questions.
- [x] Add a docs-policy exemption registry if intentionally unindexed docs files become common.
- [x] Consider moving Markdown policy helpers into `tests/docs_policy_helpers.py` if reuse grows.

### Newly Implied Docs Policy Helpers Follow-Ups

- [x] Add unit tests for Markdown helper edge cases if link parsing grows more sophisticated.
- [x] Consider supporting reference-style Markdown links if docs begin using them.
- [x] Decide whether external HTTP links should be syntax-checked or left unchecked.

### Newly Implied External Link Policy Follow-Ups

- [x] Consider adding an opt-in external link checker for release/manual maintenance, separate from default CI.

### Newly Implied External Link Checker Follow-Ups

- [x] Consider adding retry/backoff support to the manual external link checker if release checks see transient failures.

### Newly Implied External Link Checker Retry Follow-Ups

- [x] Report per-attempt retry details in verbose mode for manual release checks.
- [x] Cap maximum retry backoff for the manual external link checker.
- [x] Add external link checker allowlist/ignore file if intentionally unstable third-party URLs appear.

### Newly Implied External Link Ignore Follow-Ups

- [x] Consider requiring comments/reasons for non-comment patterns in `.external-links-ignore` if the ignore list grows.

### Newly Implied External Link Ignore Reason Follow-Ups

- [x] Consider validating `.external-links-ignore` patterns have HTTP(S) URL shape if real ignores are added.

### Newly Implied External Link Ignore Pattern Follow-Ups

- [x] Consider validating that external link ignore patterns match at least one current docs link if the ignore file gets real entries.

### Newly Implied External Link Stale Ignore Follow-Ups

- [x] Consider adding an explicit `--allow-stale-ignores` escape hatch if release maintenance ever needs to stage ignore entries before docs changes.
- [x] Consider showing the matching docs link for each ignore pattern in verbose mode if the ignore file grows.
- [x] Consider documenting wildcard semantics for `.external-links-ignore` in a dedicated maintenance doc if the checker grows further.
- [x] Consider adding expiration dates for ignored external links if the ignore list grows.
- [x] Consider reporting ignored external links in verbose mode during release checks.

### Newly Implied External Link Verbose Follow-Ups

- [x] Consider reporting successful checked links only in verbose mode once the checker scans more external links.
- [x] Consider adding quiet JSON output if release automation starts consuming external link checker results.
- [x] Add allowlist or scheme policy if docs start using non-HTTP external links intentionally.
- [x] Add duplicate-heading anchor collision handling if docs pages grow repeated headings.

### Newly Implied Duplicate Anchor Handling Follow-Ups

- [x] Consider documenting Markdown anchor compatibility assumptions if linking rules become user-facing.
- [x] Add helper coverage for non-ASCII headings if docs start using them.
- [x] Consider centralizing Markdown link parsing helpers for docs policy tests.
- [x] Add docs contribution note explaining when a docs page should be added to the index.

### Newly Implied Docs Index Guidance Follow-Ups

- [x] Consider adding a docs-index section classifier policy if `docs/index.md` grows more categories.
- [x] Add an explicit docs-index exemption list if intentional unindexed docs appear.
- [x] Add policy test checking docs links outside docs/index.md.
- [x] Add release checklist item to update docs index when adding docs pages.
- [x] Add policy test ensuring README links to core docs pages.

### Newly Implied README Core Docs Policy Follow-Ups

- [x] Consider documenting the README core-doc link set in CONTRIBUTING if the required list grows.
- [x] Consider grouping README documentation links into a dedicated Documentation section if the homepage grows longer.
- [x] Add tests that all public exceptions appear in public API docs.

### Newly Implied Public Exception Policy Follow-Ups

- [x] Add tests that public exception inheritance matches documented behavior.

### Newly Implied Public Exception Inheritance Follow-Ups

- [x] Add a structured public exception metadata table to docs.
- [x] Add doctested exception handling examples for public exception types.
- [x] Add short examples for `ConfigurationError`, `CacheKeyError`, and `CacheSerializationError`.

### Newly Implied Public Exception Examples Follow-Ups

- [x] Add public exception examples for newer decorators once implemented.
- [x] Add README link to public exception docs once centralized exception reference exists.
- [x] Add lifecycle guidance to disk backend design docs for service shutdown hooks.
- [x] Add note that decorator-bound disk backends should outlive decorated function use.
- [x] Document recommended cache file location/permissions for CLI and service use.
- [x] Add stress/smoke test for concurrent disk backend reads and writes.
- [x] Decide whether disk backend should expose cache vacuum/compaction maintenance.
- [x] Add reusable backend conformance tests for cached exception behavior, TTL, LRU, clear, and stats.
- [x] Design `RedisCacheBackend` as optional dependency extra.
- [x] Add backend conformance test suite reusable by memory/disk/redis backends.

### Newly Implied Backend Conformance Follow-Ups

- [x] Document backend conformance expectations for future backend contributors.
- [x] Document that Redis joins the conformance suite only when `RedisCacheBackend` exists.

### Newly Implied Disk Backend Lifecycle Follow-Ups

- [x] Add an executable service-shutdown example for decorator-bound disk backends.
- [x] Add platform-aware `cache_directory()` helper for repeated cache path selection.

### Newly Implied Disk Concurrency Smoke Follow-Ups

- [x] Add a heavier long-running disk concurrency stress script outside default CI.

### Newly Implied Redis Backend Design Follow-Ups

- [x] Decide Redis key prefix and stats-key naming before implementing `RedisCacheBackend`.
- [x] Add Redis optional-dependency import policy tests before the optional backend is implemented.
- [x] Reduce duplicate backend behavior tests now covered by the conformance suite.

## 4. `@retry`

- [x] Design signature.
  - [x] `attempts`
  - [x] `delay`
  - [x] `backoff`
  - [x] `max_delay`
  - [x] `jitter`
  - [x] `exceptions`
  - [x] `retry_if`
  - [x] `before_attempt`
  - [x] `after_attempt`
  - [x] `sleep`
- [x] Implement configuration validation.
- [x] Implement sync retry loop.
- [x] Implement async retry loop.
- [x] Implement exponential backoff.
- [x] Implement jitter.
- [x] Implement exception filtering.
- [x] Implement predicate-based retry decision.
- [x] Add tests for success after retry.
- [x] Add tests for exhausted attempts.
- [x] Add tests for non-retryable exceptions.
- [x] Add tests for backoff calculation.
- [x] Add tests using fake sleep to avoid slow tests.
- [x] Add async tests.
- [x] Add README example.
- [x] Add per-decorator docs.
### Newly Implied `@retry` Follow-Ups

- [x] Add tests for deterministic jitter by monkeypatching random source.
- [x] Decide to keep retry hook signatures simple until callers need richer context objects.
- [x] Add retry examples to executable docs examples.
- [x] Add executable idempotency examples for retry side-effect guidance.
- [x] Add async before/after hook support for async retry wrappers.
- [x] Document idempotency guidance for retrying side-effecting functions before public release.

## 5. `@rate_limit`

- [x] Design signature.
  - [x] `calls`
  - [x] `period`
  - [x] `key`
  - [x] `mode`: raise or block
  - [x] `clock`
  - [x] `sleep`
- [x] Decide token bucket vs sliding window implementation.
- [x] Implement global rate limit.
- [x] Implement key-based rate limit.
- [x] Implement raise mode.
- [x] Implement blocking mode.
- [x] Implement async support.
- [x] Define `RateLimitExceeded` exception.
- [x] Add tests for allowed calls.
- [x] Add tests for exceeded calls.
- [x] Add tests for window reset.
- [x] Add tests for key-based isolation.
- [x] Add tests with fake clock/sleep.
- [x] Add README example.
- [x] Add per-decorator docs.

### Newly Implied `@rate_limit` Follow-Ups

- [x] Add tests for concurrent sync callers sharing a rate-limit bucket.
- [x] Consider a structured `RateLimitExceeded` retry-after attribute if callers need machine-readable delays.
- [x] Add idempotency and distributed-limiter caveats before public release.
- [x] Add cleanup of idle keyed buckets so long-running keyed limiters do not retain expired buckets forever.
- [x] Add executable docs examples for `@rate_limit`.

## 6. `@timeout`

- [x] Design signature.
  - [x] `seconds`
  - [x] `message`
  - [x] `exception`
- [x] Define timeout exception.
- [x] Implement async timeout using `asyncio.wait_for`.
- [x] Evaluate sync timeout strategies.
  - [x] Signal-based Unix timeout.
  - [x] Thread-based timeout with documented limitations.
  - [x] Explicitly async-only for first release.
- [x] Choose conservative sync behavior.
- [x] Add tests for async timeout success.
- [x] Add tests for async timeout failure.
- [x] Add tests for metadata preservation.
- [x] Add docs warning about sync limitations.
- [x] Add README example.

### Newly Implied `@timeout` Follow-Ups

- [x] Add tests proving timed-out coroutines receive cancellation.
- [x] Document custom timeout exception constructor compatibility.
- [x] Add executable docs examples for `@timeout`.
- [x] Revisit sync timeout support with explicit platform/cancellation constraints decision record.

## 7. Observability Decorators Backlog

### `@log_calls`

- [x] Design signature.
- [x] Add argument redaction support.
- [x] Add return value redaction/summarization.
- [x] Add exception logging.
- [x] Add duration logging.
- [x] Add sync tests.
- [x] Add async tests.
- [x] Add security docs.


### Newly Implied `@log_calls` Follow-Ups

- [x] Support positional argument redaction by parameter name using `inspect.signature`.
- [x] Consider structured log record extras for function name, duration, and outcome if logging integrations need machine-readable fields.
- [x] Add executable docs examples for `@log_calls`.
- [x] Add async-safe result summarizers for async `@log_calls` wrappers.
### `@measure_time`

- [x] Design signature.
- [x] Add callback support.
- [x] Add logger support.
- [x] Add metrics hook support.
- [x] Add sync tests.
- [x] Add async tests.
- [x] Add examples.


### Newly Implied `@measure_time` Follow-Ups

- [x] Consider structured logger extras for duration/success fields if logging integrations request them.
- [x] Add async callback/metrics hook support for async `@measure_time` wrappers.
- [x] Add executable docs examples for `@measure_time`.
- [x] Consider monotonic-clock source documentation if timing precision questions recur.
## 8. Validation and Configuration Decorators Backlog

### `@validate_types`

- [x] Decide whether to use standard-library type inspection only.
- [x] Support basic built-in types.
- [x] Support `Optional`/union types.
- [x] Support return value validation option.
- [x] Add clear validation error messages.
- [x] Add tests.
- [x] Document limitations.


### Newly Implied `@validate_types` Follow-Ups

- [x] Add opt-in deep container validation with clear limitations.
- [x] Support lightweight `Literal` and `Annotated` validation.
- [x] Add executable docs examples for `@validate_types`.
- [x] Add package-specific `ValidationError` while preserving `TypeError` compatibility.
### `@require_env`

- [x] Design signature.
- [x] Support required variable names.
- [x] Support custom validators.
- [x] Support loading only at call time.
- [x] Add tests with patched environment.
- [x] Add CLI/script examples.


### Newly Implied `@require_env` Follow-Ups

- [x] Consider custom error messages for required environment variables if CLI UX needs them.
- [x] Consider optional empty-string rejection semantics if users want non-empty environment values by default.
- [x] Add executable docs examples for `@require_env`.
- [x] Wrap validator exceptions in `EnvRequirementError` with the original exception preserved as `__cause__`.
## 9. Resilience Decorators Backlog

### `@circuit_breaker`

- [x] Design signature.
- [x] Define states: closed, open, half-open.
- [x] Track failure counts.
- [x] Track reset timeout.
- [x] Support exception filters.
- [x] Add sync support.
- [x] Add async support.
- [x] Add tests with fake clock.
- [x] Add docs with service-client examples.


### Newly Implied `@circuit_breaker` Follow-Ups

- [x] Add circuit state inspection helpers on decorated functions for observability.
- [x] Consider thread-safety guards if decorated functions are used from multiple threads.
- [x] Decide to keep circuit-breaker fallback callbacks outside the decorator until callers request built-in fallback behavior.
- [x] Add executable docs examples for `@circuit_breaker`.
## 10. Documentation Backlog

- [x] Write README quick start.
- [x] Add installation instructions.
- [x] Add one example per first-release decorator.
- [x] Add decorator comparison table or bullet list.
- [x] Add security notes.
- [x] Add async usage notes.
- [x] Add timeout limitations note.
- [x] Add contributing guide.
- [x] Add release process notes.
- [x] Add API reference documentation.


### Newly Implied Documentation Follow-Ups

- [x] Expand API reference with exact parameter defaults if public signatures change before release.
- [x] Add a decorator-composition guide if users ask about stacking order.
- [x] Add executable README snippets for every first-release decorator.
- [x] Add a security hardening page if cache/logging/validation warnings keep growing.
## 11. Quality Backlog

- [x] Add unit test coverage target.
- [x] Add coverage reporting.
- [x] Add type checking gate.
- [x] Add linting gate.
- [x] Add formatting gate.
- [x] Add packaging build check.
- [x] Add import smoke test.
- [x] Add examples smoke test.
- [x] Add pre-commit configuration if useful.


### Newly Implied Quality Follow-Ups

- [x] Upload coverage XML from CI as a workflow artifact.
- [x] Add clean-wheel smoke test in an isolated venv before release.
- [x] Consider adding coverage summary comments if pull-request reporting becomes useful.
- [x] Run pre-commit in CI before explicit lint/type/test gates.
- [x] Add quality-gates docs page for local verification commands.
## 12. Release Backlog

- [x] Confirm PyPI package name availability.
- [x] Add package metadata.
- [x] Add project URLs.
- [x] Add classifiers.
- [x] Add license file.
- [x] Add versioning strategy.
- [x] Add release checklist.

### Newly Implied Release Checklist Follow-Ups

- [x] Add clean-venv local wheel install smoke test script.
- [x] Add TestPyPI/PyPI publishing instructions once package credentials and repository location are finalized.
- [x] Add git tag naming convention for releases.
- [x] Build package locally.
- [x] Test install from local wheel.
- [ ] Run `python scripts/check_package_name_availability.py` immediately before TestPyPI/PyPI publish.
- [ ] Publish test release to TestPyPI.
- [ ] Publish `v0.1.0` to PyPI when ready.


### Newly Implied Release Blockers / Follow-Ups

- [x] Choose a new PyPI distribution name because `useful-decorators` is already occupied on PyPI.
- [x] Update `pyproject.toml` package name after Russ chooses the distribution name.
- [x] Re-check PyPI/TestPyPI availability for the chosen name before publishing.
- [x] Add trusted publishing / API token instructions once the repository and package name are final.
- [x] Add repeatable checker to re-check `blakemere-decorators` availability immediately before final publish.
- [ ] Configure GitHub protected environments `testpypi` and `pypi` before running release workflow.
- [x] Add a release workflow for trusted publishing once GitHub environment names are confirmed.
- [x] Add executable composition examples.

## 13. Dogfood Backlog

- [x] Add dogfood plan and findings log.
- [x] Add local wheel dogfood harness.
- [x] Add realistic decorator-composition dogfood scenario.
- [x] Run dogfood scenario from an installed wheel.
- [x] Dogfood in a real non-demo local project before public release.
- [x] Record API/documentation annoyances from real usage.
- [x] Resolve or explicitly defer dogfood findings before TestPyPI.
- [x] Add decorator-composition guidance based on dogfood wrapper-order findings.

## 14. Future Ideas

- [x] Optional Redis-backed cache.
- [x] Optional OpenTelemetry integration.
- [x] Optional Prometheus metrics integration.
- [x] Optional structlog integration.
- [x] Django/FastAPI examples.
- [x] CLI examples.
- [x] Benchmark suite.
- [x] Documentation site plan.

## Newly Implied Writing Style Follow-Ups

- [x] Review all existing Markdown documentation against `WRITING_STYLE.md` and document findings.
- [x] Add a short project documentation style note to `CONTRIBUTING.md`, pointing contributors at `WRITING_STYLE.md` and summarizing local expectations.
- [x] Tighten the opening sections of `docs/PUBLIC_API.md`, `docs/API_REFERENCE.md`, and `docs/API_DESIGN.md` so they explain the practical decision each document supports.
- [x] Add failure-mode examples to `docs/composition.md`, `docs/timeout.md`, `docs/rate_limit.md`, and `docs/circuit_breaker.md`.
- [ ] Reflow long prose lines opportunistically when editing docs; avoid a noisy repo-wide wrap-only change unless explicitly requested.
- [ ] Revisit `docs/redis_backend_design.md` with an operating-model pass before implementing Redis support.
