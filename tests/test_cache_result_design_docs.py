from pathlib import Path


def test_cache_result_design_doc_covers_required_decisions() -> None:
    text = Path("docs/cache_result.md").read_text()

    for required in [
        "ttl",
        "maxsize",
        "key",
        "typed",
        "cache_exceptions",
        "clock",
        "Do **not** wrap or extend `functools.lru_cache`",
        "cache_clear()",
        "cache_info()",
        "threading.RLock",
    ]:
        assert required in text
