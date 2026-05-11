"""Executable examples for DiskCacheBackend documentation."""

from pathlib import Path

from useful_decorators import DiskCacheBackend, cache_result

_CALLS = 0


def fetch_user_display_name(user_id: str) -> str:
    """Pretend to fetch a user display name from an expensive source."""

    global _CALLS
    _CALLS += 1
    return f"User {user_id}"


def disk_cache_example(cache_path: Path) -> tuple[str, str, int]:
    """Run the README-style DiskCacheBackend example."""

    global _CALLS
    _CALLS = 0
    backend = DiskCacheBackend(cache_path, ttl=3600, maxsize=10_000)

    @cache_result(backend=backend, namespace="users")
    def load_user_display_name(user_id: str) -> str:
        return fetch_user_display_name(user_id)

    try:
        first = load_user_display_name("user-123")
        second = load_user_display_name("user-123")
        return first, second, _CALLS
    finally:
        backend.close()


def scoped_disk_cache_example(cache_path: Path) -> tuple[str | None, int]:
    """Use DiskCacheBackend as a short scoped cache without a decorator."""

    with DiskCacheBackend(cache_path, ttl=60, maxsize=16) as backend:
        backend.set_value("answer", "cached")
        entry = backend.get("answer")
        info = backend.info()
        return (entry.payload if entry is not None else None), info.hits
