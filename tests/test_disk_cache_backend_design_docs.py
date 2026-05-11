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
