"""Executable examples for using decorators in small CLI-style tools."""

from __future__ import annotations

from pathlib import Path

from useful_decorators import (
    DiskCacheBackend,
    cache_directory,
    cache_namespace,
    cache_result,
    retry,
)


def resolve_cache_path(app_name: str, *, base_path: Path) -> Path:
    """Resolve a cache file path without creating directories as a side effect."""

    return cache_directory(app_name, base_path=base_path) / "cache.sqlite3"


def cached_cli_lookup_example(cache_path: Path) -> tuple[str, str, int]:
    """Cache an expensive CLI lookup across repeated command calls."""

    calls = 0
    backend = DiskCacheBackend(cache_path, ttl=300, maxsize=64)

    @cache_result(backend=backend, namespace=cache_namespace("cli-users", 1))
    @retry(attempts=2, delay=0)
    def lookup_user(user_id: str) -> str:
        nonlocal calls
        calls += 1
        return f"user:{user_id}"

    try:
        first = lookup_user("123")
        second = lookup_user("123")
        return first, second, calls
    finally:
        backend.close()


def cli_main_style_example(cache_path: Path, user_id: str) -> int:
    """Return a process-style status code from a decorated CLI operation."""

    backend = DiskCacheBackend(cache_path, ttl=60, maxsize=8)

    @cache_result(backend=backend, namespace=cache_namespace("cli-main", 1))
    def load_user(user_id: str) -> str:
        if not user_id:
            raise ValueError("user id is required")
        return f"loaded:{user_id}"

    try:
        load_user(user_id)
    except ValueError:
        return 2
    finally:
        backend.close()
    return 0
