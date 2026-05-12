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


def test_cache_result_design_doc_covers_request_coalescing_design() -> None:
    text = Path("docs/cache_result.md").read_text()

    for required in [
        "## Request coalescing design",
        "coalesce_misses=True",
        "per generated cache key",
        "first thread",
        "producer",
        "wait on an in-flight marker",
        "re-check the backend after the producer finishes",
        "must not block calls for different cache keys",
        "removed in a `finally` block",
        "cache_exceptions=False",
        "cache_exceptions=True",
        "threading.Condition",
        "threading.Event",
        "separate from backend internals",
        "Never hold the in-flight lock while running user code",
        "process-local only",
        "wrapper-local",
    ]:
        assert required in text


def test_cache_result_design_doc_covers_backend_conformance_expectations() -> None:
    text = Path("docs/cache_result.md").read_text()

    for required in [
        "## Backend conformance expectations",
        "CacheBackend",
        "conformance suite",
        "get() returning `None` for misses",
        "`set_value()` replacing previous values",
        "`set_exception()` preserving cached exception payloads",
        "TTL expiry behavior",
        "max-size/LRU eviction semantics",
        "`clear()` removing entries and resetting statistics",
        "CacheInfo",
        "thread-safe access",
        "storage-specific tests",
    ]:
        assert required in text


def test_cache_result_design_doc_covers_redis_optional_extra_design() -> None:
    text = Path("docs/cache_result.md").read_text()

    for required in [
        "## Redis backend optional-extra design",
        "optional dependency extra",
        "useful-decorators[redis]",
        "redis>=5",
        "base package remains standard-library-only",
        "CacheBackend semantics",
        "CacheSerializer",
        "explicit namespace/prefix",
        "Redis TTL primitives",
        "CacheInfo",
        "network latency",
        "Redis as a hard dependency",
    ]:
        assert required in text
