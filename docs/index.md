# Documentation Index

Start here when navigating the Useful Decorators documentation.

## Core project docs

- [Public API policy](PUBLIC_API.md) — exported API, compatibility policy, and public API notes.
- [Public exceptions](exceptions.md) — public exception hierarchy, inheritance, and handling examples.
- [API design notes](API_DESIGN.md) — broader API design guidance for decorators.

## Decorator docs

- [`@deprecated`](deprecated.md) — deprecation decorator behavior and examples.
- [`@cache_result`](cache_result.md) — cache decorator behavior, backend semantics, serializer design, and lifecycle notes.

## Cache backend docs

- [`DiskCacheBackend`](disk_cache_backend.md) — SQLite-backed cache design, persistence, trust boundaries, WAL/busy-timeout behavior, and context-manager usage.

## Executable examples

Executable documentation examples live under [`examples/`](examples/):

- [`deprecated_examples.py`](examples/deprecated_examples.py)
- [`disk_cache_backend_examples.py`](examples/disk_cache_backend_examples.py)
- [`public_exception_examples.py`](examples/public_exception_examples.py)

These examples are exercised by the test suite so documentation drift gets caught before it mutates into folklore.

Executable example conventions are documented in [CONTRIBUTING.md](../CONTRIBUTING.md#executable-documentation-examples).
