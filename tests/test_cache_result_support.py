from useful_decorators import CacheInfo, CacheKeyError, MemoryCacheBackend
from useful_decorators.cache_result import _CacheEntry
from useful_decorators.exceptions import UsefulDecoratorsError


def test_cache_info_public_shape() -> None:
    info = CacheInfo(hits=2, misses=3, maxsize=128, currsize=4)

    assert info.hits == 2
    assert info.misses == 3
    assert info.maxsize == 128
    assert info.currsize == 4


def test_cache_info_is_immutable() -> None:
    info = CacheInfo(hits=0, misses=0, maxsize=None, currsize=0)

    try:
        info.hits = 1  # type: ignore[misc]
    except Exception as exc:
        assert isinstance(exc, (AttributeError, TypeError))
    else:  # pragma: no cover - defensive; frozen dataclass should prevent this
        raise AssertionError("CacheInfo should be immutable")


def test_cache_entry_internal_shape() -> None:
    entry = _CacheEntry(payload="value", expires_at=12.5)

    assert entry.payload == "value"
    assert entry.expires_at == 12.5
    assert not entry.is_exception


def test_cache_key_error_is_type_error_and_package_error() -> None:
    error = CacheKeyError("unhashable cache key")

    assert isinstance(error, TypeError)
    assert isinstance(error, UsefulDecoratorsError)


def test_memory_cache_backend_tracks_values_and_stats() -> None:
    backend = MemoryCacheBackend(maxsize=2)

    assert backend.get("missing") is None
    backend.set_value("key", "value")

    entry = backend.get("key")
    assert entry is not None
    assert entry.payload == "value"
    assert backend.info() == CacheInfo(hits=1, misses=1, maxsize=2, currsize=1)


def test_memory_cache_backend_clear_resets_entries_and_stats() -> None:
    backend = MemoryCacheBackend()

    assert backend.get("missing") is None
    backend.set_value("key", "value")
    backend.clear()

    assert backend.info() == CacheInfo(hits=0, misses=0, maxsize=128, currsize=0)


def test_memory_cache_backend_implements_cache_backend_protocol() -> None:
    from useful_decorators import CacheBackend

    assert isinstance(MemoryCacheBackend(), CacheBackend)
