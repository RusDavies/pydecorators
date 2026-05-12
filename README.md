# Useful Decorators

A focused Python library of useful decorators for everyday reliability, caching, rate limiting, timeouts, and developer ergonomics.

The goal is to provide small, typed, well-tested decorators that work in scripts, CLIs, services, and libraries without requiring a framework or a dependency shrubbery.

## Planned first release

The initial `v0.1.0` scope is:

- `@deprecated` — implemented
- `@cache_result` — sync/disk backend implemented
- `@retry` — implemented
- `@rate_limit` — implemented
- `@timeout`


## Quick example

```python
from useful_decorators import deprecated


@deprecated("Kept for compatibility.", replacement="new_function", version="0.1.0")
def old_function() -> str:
    return "still works"
```

## Development status

Pre-alpha. The project foundation exists and `@deprecated`, `@cache_result`, `@retry`, and `@rate_limit` are implemented.

Warnings use `DeprecationWarning` by default, which Python may hide depending on warning filters. See `docs/deprecated.md` for details.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

## Public API and contributing

See `docs/index.md` for the documentation index, `docs/PUBLIC_API.md` for the public API policy, `docs/API_DESIGN.md` for broader API design notes, `docs/exceptions.md` for public exception behavior, and `CONTRIBUTING.md` for the new-decorator checklist. Executable documentation examples live under `docs/examples/`.

## Release process

See `RELEASE.md` for the release checklist.

## Decorator design docs

See `docs/cache_result.md` for the cache decorator design, `docs/retry.md` for retry behavior, and `docs/rate_limit.md` for rate limiting.

### Retry example

```python
from useful_decorators import retry


@retry(attempts=3, delay=0.25, backoff=2, exceptions=ConnectionError)
def call_service() -> str:
    return "ok"
```

`@retry` supports sync and async functions, exception filtering, predicate-based retry decisions, attempt hooks, jitter, max-delay caps, and injectable sleep functions for fast tests.

### Rate-limit example

```python
from useful_decorators import rate_limit


@rate_limit(calls=10, period=60, key=lambda user_id: user_id)
def call_user_api(user_id: str) -> str:
    return "ok"
```

`@rate_limit` uses an in-process sliding window and supports global or keyed buckets, raise or block mode, async functions, and injectable clocks/sleep functions for tests.

### Cache example

```python
from useful_decorators import cache_result


@cache_result(maxsize=128)
def expensive_lookup(value: str) -> str:
    return value.upper()
```

`@cache_result` uses `MemoryCacheBackend` by default and also includes `DiskCacheBackend` for trusted local persistent caches. Future backend work is planned for Redis storage.

Shared cache backends can be isolated with `namespace=` when multiple decorated functions use the same backend. TTL is fixed from write time by default; pass `refresh_ttl_on_hit=True` to `@cache_result` or a backend when hot entries should use sliding expiry. Pass `coalesce_misses=True` to `@cache_result` when duplicate concurrent misses for the same key should share one in-flight computation.

For a trusted local persistent cache, create one `DiskCacheBackend`, pass it to `@cache_result`, and close it when your script or service shuts down:

```python
from pathlib import Path

from useful_decorators import DiskCacheBackend, cache_result

backend = DiskCacheBackend(
    Path(".cache/useful-decorators.sqlite3"),
    ttl=3600,
    maxsize=10_000,
)


@cache_result(backend=backend, namespace="users")
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
