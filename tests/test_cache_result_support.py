import pytest

from useful_decorators import (
    CacheInfo,
    CacheKeyError,
    DiskCacheDropEvent,
    JsonCacheSerializer,
    MemoryCacheBackend,
    PickleCacheSerializer,
)
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


def test_disk_cache_drop_event_public_shape() -> None:
    error = ValueError("bad row")
    event = DiskCacheDropEvent(
        key="key",
        reason="payload_deserialization_error",
        expected_serializer_content_type="application/python-pickle",
        actual_serializer_content_type="application/python-pickle",
        exception=error,
    )

    assert event.key == "key"
    assert event.reason == "payload_deserialization_error"
    assert event.expected_serializer_content_type == "application/python-pickle"
    assert event.actual_serializer_content_type == "application/python-pickle"
    assert event.exception is error


def test_cache_entry_internal_shape() -> None:
    entry = _CacheEntry(payload="value", expires_at=12.5)

    assert entry.payload == "value"
    assert entry.expires_at == 12.5
    assert not entry.is_exception


def test_cache_key_error_is_type_error_and_package_error() -> None:
    error = CacheKeyError("unhashable cache key")

    assert isinstance(error, TypeError)
    assert isinstance(error, UsefulDecoratorsError)


def test_memory_cache_backend_implements_cache_backend_protocol() -> None:
    from useful_decorators import CacheBackend

    assert isinstance(MemoryCacheBackend(), CacheBackend)


def test_memory_cache_backend_can_refresh_ttl_on_hit() -> None:
    clock = MutableSupportClock()
    backend = MemoryCacheBackend(ttl=10, refresh_ttl_on_hit=True, clock=clock)

    backend.set_value("key", "value")
    clock.advance(9)
    assert backend.get("key") is not None
    clock.advance(9)
    assert backend.get("key") is not None
    clock.advance(10)
    assert backend.get("key") is None


class MutableSupportClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_pickle_cache_serializer_round_trips_python_objects() -> None:
    serializer = PickleCacheSerializer()
    payload = {"numbers": [1, 2, 3], "nested": {"ok": True}}

    assert serializer.loads(serializer.dumps(payload)) == payload
    assert serializer.content_type == "application/python-pickle"


def test_json_cache_serializer_round_trips_json_compatible_values() -> None:
    serializer = JsonCacheSerializer()
    payload = {"name": "café", "numbers": [1, 2, 3], "nested": {"ok": True}}

    serialized = serializer.dumps(payload)

    assert serialized == b'{"name":"caf\xc3\xa9","numbers":[1,2,3],"nested":{"ok":true}}'
    assert serializer.loads(serialized) == payload
    assert serializer.content_type == "application/json"


def test_json_cache_serializer_implements_serializer_protocol() -> None:
    from useful_decorators import CacheSerializer

    assert isinstance(JsonCacheSerializer(), CacheSerializer)


def test_json_cache_serializer_wraps_serialization_failures() -> None:
    from useful_decorators import CacheSerializationError

    serializer = JsonCacheSerializer()

    with pytest.raises(CacheSerializationError, match="failed to serialize cache value"):
        serializer.dumps({"not-json": object()})


def test_json_cache_serializer_rejects_non_finite_numbers() -> None:
    from useful_decorators import CacheSerializationError

    serializer = JsonCacheSerializer()

    with pytest.raises(CacheSerializationError, match="failed to serialize cache value"):
        serializer.dumps(float("nan"))


def test_json_cache_serializer_wraps_deserialization_failures() -> None:
    from useful_decorators import CacheSerializationError

    serializer = JsonCacheSerializer()

    with pytest.raises(CacheSerializationError, match="failed to deserialize cache value"):
        serializer.loads(b"not json")


def test_pickle_cache_serializer_implements_serializer_protocol() -> None:
    from useful_decorators import CacheSerializer

    assert isinstance(PickleCacheSerializer(), CacheSerializer)


def test_pickle_cache_serializer_wraps_serialization_failures() -> None:
    from useful_decorators import CacheSerializationError

    serializer = PickleCacheSerializer()

    with pytest.raises(CacheSerializationError, match="failed to serialize cache value"):
        serializer.dumps(lambda value: value)


def test_pickle_cache_serializer_wraps_deserialization_failures() -> None:
    from useful_decorators import CacheSerializationError

    serializer = PickleCacheSerializer()

    with pytest.raises(CacheSerializationError, match="failed to deserialize cache value"):
        serializer.loads(b"not pickle")
