# PyDecorators

A focused Python library of useful decorators for everyday reliability, caching, rate limiting, timeouts, and developer ergonomics.

The goal is to provide small, typed, well-tested decorators that work in scripts, CLIs, services, and libraries without requiring a framework or a dependency shrubbery.

## What is included

`v0.1.1` includes the same public API as `v0.1.0`, with cleaned post-release documentation:

- `@deprecated` for compatibility warnings.
- `@cache_result` with in-memory and disk-backed caching.
- `@retry` for transient failures.
- `@rate_limit` for simple in-process throttling.
- `@timeout` for async timeout boundaries.
- `@log_calls` and `@measure_time` for lightweight observability.
- `@validate_types` for runtime argument checks.
- `@require_env` for environment preflight checks.
- `@circuit_breaker` for failing-fast around unhealthy dependencies.

## Installation

Install from PyPI:

```bash
python -m pip install blakemere-wraptools
```

The distribution name is `blakemere-wraptools`; the import package is `pydecorators`:

```python
from pydecorators import retry
```

For local development:

```bash
python -m pip install -e '.[dev]'
```

## Quick start

Pick the smallest decorator that solves the immediate problem:

```python
from pydecorators import retry


@retry(attempts=3, delay=0.25, backoff=2, exceptions=(ConnectionError, TimeoutError))
def call_service() -> str:
    return "ok"
```

Then read the per-decorator docs and `docs/composition.md` before stacking decorators together. Decorator soup is still soup, even when typed.

## Development status

Released as `blakemere-wraptools` `0.1.1`. The public API is still pre-1.0: useful, tested, and documented, but compatibility can change when the library needs to get less weird.

Warnings use `DeprecationWarning` by default, which Python may hide depending on warning filters. See `docs/deprecated.md` for details.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
python scripts/smoke_imports.py
python scripts/smoke_examples.py
pytest
python -m build
python scripts/smoke_wheel_install.py
python scripts/dogfood_local_wheel.py
python scripts/dogfood_external_project.py
```

`pytest` enforces coverage for `pydecorators` with terminal and XML coverage reports.

Optional local pre-commit hooks are available:

```bash
pre-commit install
pre-commit run --all-files
```

## Dogfooding and release checks

Dogfood scenarios remain part of the release gate. Run them before cutting a new release:

```bash
python scripts/dogfood_local_wheel.py
python scripts/dogfood_external_project.py
```

## Documentation

Start with the [documentation index](docs/index.md), or jump straight to the guide you need:

- [API reference](docs/API_REFERENCE.md): public decorators, backends, serializers, result types, and exceptions.
- [API design notes](docs/API_DESIGN.md): the conventions behind decorator signatures, typing, and exports.
- [Public API and compatibility](docs/PUBLIC_API.md): what is stable, what is internal, and what pre-1.0 compatibility means.
- [Decorator composition](docs/composition.md): practical guidance for stacking decorators without making soup.
- [Exceptions](docs/exceptions.md): the public exception hierarchy and when each error is raised.
- [Security hardening](docs/security_hardening.md): cache, logging, validation, and environment-safety notes.
- [Contributing](CONTRIBUTING.md): how to add decorators, docs, tests, and release checks.

Executable examples are collected in [docs/examples](docs/examples/).

## Release process

See `RELEASE.md` for the release checklist.

## Decorator design docs

See `docs/cache_result.md` for the cache decorator design, `docs/retry.md` for retry behavior, `docs/rate_limit.md` for rate limiting, `docs/timeout.md` for async timeout behavior, `docs/log_calls.md` for call logging, `docs/measure_time.md` for timing hooks, `docs/validate_types.md` for lightweight runtime type validation, `docs/require_env.md` for environment checks, `docs/circuit_breaker.md` for circuit-breaker behavior, `docs/composition.md` for stacking guidance, and `docs/API_REFERENCE.md` for a compact API reference.

## Decorator overview

- `@deprecated`: warn when old APIs are used.
- `@cache_result`: cache expensive sync results in memory or trusted local disk storage.
- `@retry`: retry transient failures with explicit policy.
- `@rate_limit`: enforce in-process sliding-window call limits.
- `@timeout`: apply async deadlines using `asyncio.wait_for`.
- `@log_calls`: log calls, durations, exceptions, and optional summaries.
- `@measure_time`: emit timing data to callbacks, loggers, or metrics hooks.
- `@validate_types`: shallow runtime checks for simple annotations.
- `@require_env`: check environment requirements at call time.
- `@circuit_breaker`: stop hammering a failing dependency until a reset window opens.

## Security and operational notes

See `docs/security_hardening.md` for the centralized hardening checklist.

- Treat `DiskCacheBackend` files as trusted local data. The default pickle serializer must not load untrusted cache databases.
- Do not put disk cache files in world-writable directories.
- Keep cache values disposable; use namespaces or clear caches when semantics change.
- Argument/result logging is opt-in because logs preserve secrets with the enthusiasm of a museum curator.
- `@validate_types` is not a schema validator or security boundary.
- `@rate_limit` and `@circuit_breaker` are in-process only; they do not coordinate across workers, containers, or hosts.
- Environment checks protect configuration mistakes, not secret storage. Use proper secret-management systems for real secrets.

## Async support notes

- `@deprecated`, `@retry`, `@rate_limit`, `@timeout`, `@log_calls`, `@measure_time`, `@validate_types`, `@require_env`, and `@circuit_breaker` support async callables.
- `@cache_result` is sync-only for now.
- `@timeout` is deliberately async-only. Sync timeout strategies based on signals or worker threads have sharp edges, so sync functions currently raise `ConfigurationError` instead of pretending the problem is easy.

### Deprecated example

```python
from pydecorators import deprecated


@deprecated("Kept for compatibility.", replacement="new_function", version="0.1.0")
def old_function() -> str:
    return "still works"
```

### Retry example

```python
from pydecorators import retry


@retry(attempts=3, delay=0.25, backoff=2, exceptions=ConnectionError)
def call_service() -> str:
    return "ok"
```

`@retry` supports sync and async functions, exception filtering, predicate-based retry decisions, attempt hooks, jitter, max-delay caps, and injectable sleep functions for fast tests.

### Rate-limit example

```python
from pydecorators import rate_limit


@rate_limit(calls=10, period=60, key=lambda user_id: user_id)
def call_user_api(user_id: str) -> str:
    return "ok"
```

`@rate_limit` uses an in-process sliding window and supports global or keyed buckets, raise or block mode, async functions, and injectable clocks/sleep functions for tests.

### Timeout example

```python
from pydecorators import timeout


@timeout(seconds=2)
async def fetch_user(user_id: str) -> str:
    return user_id
```

`@timeout` currently supports async functions using `asyncio.wait_for`. Sync functions are rejected deliberately until a safe, well-documented sync timeout strategy exists.

### Logging example

```python
from pydecorators import log_calls


@log_calls(include_args=True, redact_args={"password"})
def authenticate(*, username: str, password: str) -> bool:
    return bool(username and password)
```

`@log_calls` logs start/finish duration and exceptions by default. Argument and result logging are opt-in; use redaction and summaries carefully because logs are where secrets go to become immortal.

### Timing example

```python
from pydecorators import TimingInfo, measure_time


timings: list[TimingInfo] = []


@measure_time(callback=timings.append)
def rebuild_index() -> None:
    pass
```

`@measure_time` records sync and async durations through optional callback, logger, or metrics hooks.

### Type-validation example

```python
from pydecorators import validate_types


@validate_types(validate_return=True)
def double(value: int) -> int:
    return value * 2
```

`@validate_types` provides lightweight, shallow runtime checks for simple annotations. It is not a full schema validator; sometimes the boring warning label is the difference between a tool and a liability.

### Environment requirement example

```python
from pydecorators import require_env


@require_env("API_TOKEN")
def call_service() -> str:
    return "ok"
```

`@require_env` checks variables at call time, so tests and deployment systems can patch environment state after import.

### Circuit-breaker example

```python
from pydecorators import CircuitBreakerOpen, circuit_breaker


@circuit_breaker(failure_threshold=2, reset_timeout=10)
def call_vendor_api() -> str:
    return "ok"


try:
    call_vendor_api()
except CircuitBreakerOpen:
    pass
```

`@circuit_breaker` is an in-process breaker with closed, open, and half-open states. Useful, not magic. Architecture remains annoyingly undefeated.

### Cache example

```python
from pydecorators import cache_result


@cache_result(maxsize=128)
def expensive_lookup(value: str) -> str:
    return value.upper()
```

`@cache_result` uses `MemoryCacheBackend` by default and also includes `DiskCacheBackend` for trusted local persistent caches. Future backend work is planned for Redis storage.

Shared cache backends can be isolated with `namespace=` when multiple decorated functions use the same backend. For persistent disk caches, treat namespace names and custom key functions as part of the cache file's compatibility contract: changing either one can strand old entries, collide with another decorated function, or return values computed under older semantics. Use explicit namespaces for long-lived caches, keep custom key functions stable across releases, and clear or rotate the cache when function behavior, argument meaning, serializer format, or namespace strategy changes.

TTL is fixed from write time by default; pass `refresh_ttl_on_hit=True` to `@cache_result` or a backend when hot entries should use sliding expiry. Fixed TTL is better for predictable freshness and retention: an entry expires at a known time even if it is popular. Sliding TTL is better for expensive hot data that may stay cached while traffic continues, but it can keep stale or sensitive values alive indefinitely unless you also bound cache size, choose conservative TTLs, and clear caches when semantics change. Pass `coalesce_misses=True` to `@cache_result` when duplicate concurrent misses for the same key should share one in-flight computation.

A simple cache-versioning recipe is to include an application-controlled version in the namespace, such as `namespace="users:v1"`, and bump it to `users:v2` when cached value shape, authorization assumptions, serializer behavior, or key semantics change. That intentionally abandons old rows without needing to parse or migrate them. For larger applications, keep the version string near the code that defines the cached value contract, not buried in a random decorator where future-you will absolutely forget it.

For a trusted local persistent cache, create one `DiskCacheBackend`, pass it to `@cache_result`, and close it when your script or service shuts down:

```python
from pathlib import Path

from pydecorators import DiskCacheBackend, cache_namespace, cache_result

backend = DiskCacheBackend(
    Path(".cache/pydecorators.sqlite3"),
    ttl=3600,
    maxsize=10_000,
)


@cache_result(backend=backend, namespace=cache_namespace("users", 1))
def load_user_display_name(user_id: str) -> str:
    return fetch_user_display_name(user_id)


try:
    print(load_user_display_name("user-123"))
finally:
    backend.close()
```

For long-running applications, keep the backend for the application lifetime and close it from your normal shutdown hook. For short scoped backend operations that are not decorator-bound, `DiskCacheBackend` also supports `with DiskCacheBackend(...) as backend:`.

Do **not** create a decorator-bound `DiskCacheBackend` inside a short `with` block unless all decorated calls happen before the block exits. The context manager closes the backend on exit; later calls through the decorated function raise `CacheBackendClosedError`.

Disk backend design lives in `docs/disk_cache_backend.md`; implementation uses SQLite and the cache serializer interface. The default disk payload serializer uses pickle, so cache databases must be treated as trusted local files only — do not load cache DBs from untrusted sources or place them in world-writable directories. For simple JSON-compatible payloads, use `JsonCacheSerializer` instead of pickle when values should be easier to inspect or consume from other languages.

`DiskCacheBackend` is intended for single-host local caching. It uses normal SQLite file locking, requests WAL mode by default, and configures a 5000 ms busy timeout to reduce transient `database is locked` failures. Those settings improve local reader/writer behavior, but they do not make it a distributed cache and they do not promise safe cross-host semantics on shared/network filesystems. If multiple processes use the same cache file, expect normal SQLite contention behavior and keep cached values disposable. If you need visibility into rows dropped because of serializer mismatches or corrupt payloads, pass `on_drop=` to `DiskCacheBackend` and log the `DiskCacheDropEvent`.
