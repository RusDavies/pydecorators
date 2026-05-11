# Useful Decorators

A focused Python library of useful decorators for everyday reliability, caching, rate limiting, timeouts, and developer ergonomics.

The goal is to provide small, typed, well-tested decorators that work in scripts, CLIs, services, and libraries without requiring a framework or a dependency shrubbery.

## Planned first release

The initial `v0.1.0` scope is:

- `@deprecated` — implemented
- `@cache_result` — sync core implemented
- `@retry`
- `@rate_limit`
- `@timeout`


## Quick example

```python
from useful_decorators import deprecated


@deprecated("Kept for compatibility.", replacement="new_function", version="0.1.0")
def old_function() -> str:
    return "still works"
```

## Development status

Pre-alpha. The project foundation exists and `@deprecated` is implemented.

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

See `docs/PUBLIC_API.md` for the public API policy and `CONTRIBUTING.md` for the new-decorator checklist. Executable documentation examples live under `docs/examples/`.

## Release process

See `RELEASE.md` for the release checklist.

## Decorator design docs

See `docs/cache_result.md` for the planned cache decorator design.

### Cache example

```python
from useful_decorators import cache_result


@cache_result(maxsize=128)
def expensive_lookup(value: str) -> str:
    return value.upper()
```

`@cache_result` uses `MemoryCacheBackend` by default and also includes `DiskCacheBackend` for trusted local persistent caches. Future backend work is planned for Redis storage.

Shared cache backends can be isolated with `namespace=` when multiple decorated functions use the same backend.

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

Disk backend design lives in `docs/disk_cache_backend.md`; implementation uses SQLite and the cache serializer interface. The default disk payload serializer uses pickle, so cache databases must be treated as trusted local files only — do not load cache DBs from untrusted sources or place them in world-writable directories.

`DiskCacheBackend` is intended for single-host local caching. It uses normal SQLite file locking, requests WAL mode by default, and configures a 5000 ms busy timeout to reduce transient `database is locked` failures. Those settings improve local reader/writer behavior, but they do not make it a distributed cache and they do not promise safe cross-host semantics on shared/network filesystems. If multiple processes use the same cache file, expect normal SQLite contention behavior and keep cached values disposable.
