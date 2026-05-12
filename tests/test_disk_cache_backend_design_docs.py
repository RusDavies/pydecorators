from pathlib import Path


def test_disk_cache_backend_design_doc_covers_required_decisions() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "SQLite",
        "cache_entries",
        "cache_stats",
        "PickleCacheSerializer",
        "CacheSerializer",
        "expires_at",
        "last_accessed",
        "CacheInfo",
        "RLock",
        "check_same_thread=False",
        "Trust boundary warning",
        "pickle",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_persistent_key_stability() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "For persistent cache reuse",
        "on-disk compatibility contract",
        "stable `namespace`",
        "Changing the namespace intentionally creates a separate cache key space",
        "call arguments and keyword names stable",
        "`typed=True` consistent",
        "custom `key` function",
        "orphan old cache rows",
        "Use `clear()` or a new namespace",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_cache_versioning_guidance() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Cache versioning and schema changes",
        "persistent disk-cache reuse as a compatibility surface",
        "versioned namespace",
        "users:v1",
        "Bump the namespace",
        "cache_clear()",
        "backend `clear()`",
        "automatic schema migrations",
        "Namespace versioning",
    ]:
        assert required in text
