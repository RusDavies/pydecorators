# Documentation Index

Start here when navigating the PyDecorators documentation.

## Core project docs

- [Public API policy](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md) — exported API, compatibility policy, and public API notes.
- [Public exceptions](https://github.com/RusDavies/pydecorators/blob/master/docs/exceptions.md) — public exception hierarchy, inheritance, and handling examples.
- [API design notes](https://github.com/RusDavies/pydecorators/blob/master/docs/API_DESIGN.md) — broader API design guidance for decorators.
- [API reference](https://github.com/RusDavies/pydecorators/blob/master/docs/API_REFERENCE.md) — compact reference for exported decorators, cache APIs, data types, and exceptions.
- [Decorator composition](https://github.com/RusDavies/pydecorators/blob/master/docs/composition.md) — practical guidance for stacking wrappers and choosing retry/logging/timing/rate-limit semantics.
- [Django and FastAPI examples](https://github.com/RusDavies/pydecorators/blob/master/docs/web_frameworks.md) — framework-adjacent caching/retry placement without adding web-framework dependencies.
- [Observability integrations](https://github.com/RusDavies/pydecorators/blob/master/docs/observability_integrations.md) — OpenTelemetry, Prometheus, and structlog adapter patterns without hard dependencies.
- [Quality gates](https://github.com/RusDavies/pydecorators/blob/master/docs/quality_gates.md) — local verification commands, Hatch aliases, and release-prep gate meaning.
- [Documentation site plan](https://github.com/RusDavies/pydecorators/blob/master/docs/docs_site_plan.md) — site-generator deferral, launch checklist, and Markdown-first docs posture.
- [Future extension decisions](https://github.com/RusDavies/pydecorators/blob/master/docs/future_extension_decisions.md) — explicit deferrals for conditional API and tooling ideas.
- [Release note template](https://github.com/RusDavies/pydecorators/blob/master/docs/release_note_template.md) — compatibility wording for release notes.
- [Security hardening guide](https://github.com/RusDavies/pydecorators/blob/master/docs/security_hardening.md) — cache, logging, validation, and in-process control safety checklist.
- [Security audit 2026-05-21](https://github.com/RusDavies/pydecorators/blob/master/docs/security_audit_2026-05-21.md) — evidence-backed local audit findings and follow-up items.
- [Markdown anchor policy](https://github.com/RusDavies/pydecorators/blob/master/docs/markdown_anchor_policy.md) — heading-anchor assumptions used by docs-link policy tests.
- [Docs index exemption registry](https://github.com/RusDavies/pydecorators/blob/master/docs/docs_index_exemptions.md) — rules for intentional docs-index exclusions.
- [Writing style audit](https://github.com/RusDavies/pydecorators/blob/master/docs/writing_style_audit.md) — review of existing documentation against the project writing style.

## Decorator docs

- [`@deprecated`](https://github.com/RusDavies/pydecorators/blob/master/docs/deprecated.md) — deprecation decorator behavior and examples.
- [`@cache_result`](https://github.com/RusDavies/pydecorators/blob/master/docs/cache_result.md) — cache decorator behavior, backend semantics, serializer design, and lifecycle notes.
- [`@retry`](https://github.com/RusDavies/pydecorators/blob/master/docs/retry.md) — retry decorator behavior, backoff, filtering, hooks, and async support.
- [`@rate_limit`](https://github.com/RusDavies/pydecorators/blob/master/docs/rate_limit.md) — rate-limit decorator behavior, sliding-window policy, keyed buckets, modes, and async support.
- [`@timeout`](https://github.com/RusDavies/pydecorators/blob/master/docs/timeout.md) — async timeout decorator behavior, cancellation semantics, and sync limitations.
- [Sync timeout decision](https://github.com/RusDavies/pydecorators/blob/master/docs/sync_timeout_decision.md) — explicit platform and cancellation constraints for any future sync timeout design.
- [`@log_calls`](https://github.com/RusDavies/pydecorators/blob/master/docs/log_calls.md) — call logging decorator behavior, duration logging, argument/result controls, and security notes.
- [`@measure_time`](https://github.com/RusDavies/pydecorators/blob/master/docs/measure_time.md) — timing decorator behavior, callback/logger/metrics hooks, and `TimingInfo`.
- [`@validate_types`](https://github.com/RusDavies/pydecorators/blob/master/docs/validate_types.md) — lightweight runtime type validation behavior, supported annotations, and limitations.
- [`@require_env`](https://github.com/RusDavies/pydecorators/blob/master/docs/require_env.md) — call-time environment variable requirements, validators, and script examples.
- [`@circuit_breaker`](https://github.com/RusDavies/pydecorators/blob/master/docs/circuit_breaker.md) — in-process circuit breaker states, reset behavior, filters, and service-client examples.

## Cache backend docs

- [`DiskCacheBackend`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md) — SQLite-backed cache design, persistence, trust boundaries, WAL/busy-timeout behavior, and context-manager usage.
- [Redis backend design notes](https://github.com/RusDavies/pydecorators/blob/master/docs/redis_backend_design.md) — optional Redis backend key-prefix, stats-key, and dependency decisions before implementation.

## Executable examples

Executable documentation examples live under [`examples/`](examples/):

- [`circuit_breaker_examples.py`](examples/circuit_breaker_examples.py)
- [`cli_examples.py`](examples/cli_examples.py)
- [`composition_examples.py`](examples/composition_examples.py)
- [`deprecated_examples.py`](examples/deprecated_examples.py)
- [`disk_cache_backend_examples.py`](examples/disk_cache_backend_examples.py)
- [`log_calls_examples.py`](examples/log_calls_examples.py)
- [`measure_time_examples.py`](examples/measure_time_examples.py)
- [`observability_integration_examples.py`](examples/observability_integration_examples.py)
- [`public_exception_examples.py`](examples/public_exception_examples.py)
- [`rate_limit_examples.py`](examples/rate_limit_examples.py)
- [`readme_examples.py`](examples/readme_examples.py)
- [`require_env_examples.py`](examples/require_env_examples.py)
- [`retry_examples.py`](examples/retry_examples.py)
- [`retry_idempotency_examples.py`](examples/retry_idempotency_examples.py)
- [`timeout_examples.py`](examples/timeout_examples.py)
- [`validate_types_examples.py`](examples/validate_types_examples.py)
- [`web_framework_examples.py`](examples/web_framework_examples.py)

These examples are exercised by the test suite so documentation drift gets caught before it mutates into folklore.

Executable example conventions are documented in [CONTRIBUTING.md](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md#executable-documentation-examples).
