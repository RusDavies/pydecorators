# Documentation Index

Start here when navigating the Useful Decorators documentation.

## Core project docs

- [Public API policy](PUBLIC_API.md) — exported API, compatibility policy, and public API notes.
- [Public exceptions](exceptions.md) — public exception hierarchy, inheritance, and handling examples.
- [API design notes](API_DESIGN.md) — broader API design guidance for decorators.
- [API reference](API_REFERENCE.md) — compact reference for exported decorators, cache APIs, data types, and exceptions.

## Decorator docs

- [`@deprecated`](deprecated.md) — deprecation decorator behavior and examples.
- [`@cache_result`](cache_result.md) — cache decorator behavior, backend semantics, serializer design, and lifecycle notes.
- [`@retry`](retry.md) — retry decorator behavior, backoff, filtering, hooks, and async support.
- [`@rate_limit`](rate_limit.md) — rate-limit decorator behavior, sliding-window policy, keyed buckets, modes, and async support.
- [`@timeout`](timeout.md) — async timeout decorator behavior, cancellation semantics, and sync limitations.
- [`@log_calls`](log_calls.md) — call logging decorator behavior, duration logging, argument/result controls, and security notes.
- [`@measure_time`](measure_time.md) — timing decorator behavior, callback/logger/metrics hooks, and `TimingInfo`.
- [`@validate_types`](validate_types.md) — lightweight runtime type validation behavior, supported annotations, and limitations.
- [`@require_env`](require_env.md) — call-time environment variable requirements, validators, and script examples.
- [`@circuit_breaker`](circuit_breaker.md) — in-process circuit breaker states, reset behavior, filters, and service-client examples.

## Cache backend docs

- [`DiskCacheBackend`](disk_cache_backend.md) — SQLite-backed cache design, persistence, trust boundaries, WAL/busy-timeout behavior, and context-manager usage.

## Executable examples

Executable documentation examples live under [`examples/`](examples/):

- [`deprecated_examples.py`](examples/deprecated_examples.py)
- [`disk_cache_backend_examples.py`](examples/disk_cache_backend_examples.py)
- [`public_exception_examples.py`](examples/public_exception_examples.py)

These examples are exercised by the test suite so documentation drift gets caught before it mutates into folklore.

Executable example conventions are documented in [CONTRIBUTING.md](../CONTRIBUTING.md#executable-documentation-examples).
