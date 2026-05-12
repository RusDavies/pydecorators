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


def test_disk_cache_backend_design_doc_covers_maintenance_helper_design() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Integrity check and maintenance helper design",
        "maintain()",
        "DiskCacheMaintenanceReport",
        "prune_expired=True",
        "validate_payloads=True",
        "serializer mismatch cleanup",
        "vacuum=True",
        "rows_seen",
        "expired_rows_dropped",
        "serializer_mismatch_rows_dropped",
        "corrupt_payload_rows_dropped",
        "DiskCacheDropEvent",
        "Non-goals for the first maintenance helper",
        "repairing corrupted payloads",
        "migrating payload schemas automatically",
        "running `VACUUM` automatically",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_sqlite_column_stability() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## SQLite column stability for debugging",
        "Direct SQLite inspection is supported only as a debugging aid",
        "Debugging-friendly columns",
        "`payload`",
        "`serializer_content_type`",
        "`is_exception`",
        "`created_at`, `last_accessed`, and `expires_at`",
        "Internal implementation details",
        "`key`: an internal serialized cache key",
        "The shape of `cache_stats` is internal",
        "backend.info()",
        "cache_info()",
        "add an explicit API instead of scraping",
    ]:
        assert required in text
