# Documentation Index

Start here when navigating the Useful Decorators documentation.

## Core project docs

- [Public API policy](PUBLIC_API.md) — exported API, compatibility policy, and public API notes.
- [Public exceptions](exceptions.md) — public exception hierarchy, inheritance, and handling examples.
- [API design notes](API_DESIGN.md) — broader API design guidance for decorators.
- [API reference](API_REFERENCE.md) — compact reference for exported decorators, cache APIs, data types, and exceptions.
- [Decorator composition](composition.md) — practical guidance for stacking wrappers and choosing retry/logging/timing/rate-limit semantics.
- [Quality gates](quality_gates.md) — local verification commands, Hatch aliases, and release-prep gate meaning.
- [Release note template](release_note_template.md) — compatibility wording for release notes.
- [Security hardening guide](security_hardening.md) — cache, logging, validation, and in-process control safety checklist.
- [Markdown anchor policy](markdown_anchor_policy.md) — heading-anchor assumptions used by docs-link policy tests.
- [Docs index exemption registry](docs_index_exemptions.md) — rules for intentional docs-index exclusions.

## Decorator docs

- [`@deprecated`](deprecated.md) — deprecation decorator behavior and examples.
- [`@cache_result`](cache_result.md) — cache decorator behavior, backend semantics, serializer design, and lifecycle notes.
- [`@retry`](retry.md) — retry decorator behavior, backoff, filtering, hooks, and async support.
- [`@rate_limit`](rate_limit.md) — rate-limit decorator behavior, sliding-window policy, keyed buckets, modes, and async support.
- [`@timeout`](timeout.md) — async timeout decorator behavior, cancellation semantics, and sync limitations.
- [Sync timeout decision](sync_timeout_decision.md) — explicit platform and cancellation constraints for any future sync timeout design.
- [`@log_calls`](log_calls.md) — call logging decorator behavior, duration logging, argument/result controls, and security notes.
- [`@measure_time`](measure_time.md) — timing decorator behavior, callback/logger/metrics hooks, and `TimingInfo`.
- [`@validate_types`](validate_types.md) — lightweight runtime type validation behavior, supported annotations, and limitations.
- [`@require_env`](require_env.md) — call-time environment variable requirements, validators, and script examples.
- [`@circuit_breaker`](circuit_breaker.md) — in-process circuit breaker states, reset behavior, filters, and service-client examples.

## Cache backend docs

- [`DiskCacheBackend`](disk_cache_backend.md) — SQLite-backed cache design, persistence, trust boundaries, WAL/busy-timeout behavior, and context-manager usage.

## Executable examples

Executable documentation examples live under [`examples/`](examples/):

- [`circuit_breaker_examples.py`](examples/circuit_breaker_examples.py)
- [`composition_examples.py`](examples/composition_examples.py)
- [`deprecated_examples.py`](examples/deprecated_examples.py)
- [`disk_cache_backend_examples.py`](examples/disk_cache_backend_examples.py)
- [`log_calls_examples.py`](examples/log_calls_examples.py)
- [`measure_time_examples.py`](examples/measure_time_examples.py)
- [`public_exception_examples.py`](examples/public_exception_examples.py)
- [`rate_limit_examples.py`](examples/rate_limit_examples.py)
- [`readme_examples.py`](examples/readme_examples.py)
- [`require_env_examples.py`](examples/require_env_examples.py)
- [`retry_examples.py`](examples/retry_examples.py)
- [`retry_idempotency_examples.py`](examples/retry_idempotency_examples.py)
- [`timeout_examples.py`](examples/timeout_examples.py)
- [`validate_types_examples.py`](examples/validate_types_examples.py)

These examples are exercised by the test suite so documentation drift gets caught before it mutates into folklore.

Executable example conventions are documented in [CONTRIBUTING.md](../CONTRIBUTING.md#executable-documentation-examples).
