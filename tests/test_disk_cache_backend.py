import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from useful_decorators import DiskCacheBackend
from useful_decorators.exceptions import ConfigurationError


def table_names(path: Path) -> set[str]:
    with closing(sqlite3.connect(path)) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def test_disk_cache_backend_initializes_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "cache.sqlite3"
    backend = DiskCacheBackend(db_path)
    backend.close()

    assert db_path.exists()
    assert table_names(db_path) >= {"cache_entries", "cache_stats"}

    with closing(sqlite3.connect(db_path)) as connection:
        stats = connection.execute("SELECT id, hits, misses FROM cache_stats").fetchall()

    assert stats == [(1, 0, 0)]


def test_disk_cache_backend_schema_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"

    first = DiskCacheBackend(db_path)
    first.close()
    second = DiskCacheBackend(db_path)
    second.close()

    assert table_names(db_path) >= {"cache_entries", "cache_stats"}


def test_disk_cache_backend_rejects_invalid_configuration(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="ttl must be greater than zero"):
        DiskCacheBackend(tmp_path / "cache.sqlite3", ttl=0)
    with pytest.raises(ConfigurationError, match="maxsize must be greater than zero"):
        DiskCacheBackend(tmp_path / "cache.sqlite3", maxsize=0)


def test_disk_cache_backend_supports_context_manager(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"

    with DiskCacheBackend(db_path) as backend:
        assert backend.path == db_path

    assert db_path.exists()


def test_disk_cache_backend_serializes_keys(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        key = ("namespace", "value", 1)
        serialized = backend._serialize_key(key)

        assert isinstance(serialized, bytes)
        assert serialized == backend._serialize_key(key)
    finally:
        backend.close()


def test_disk_cache_backend_serializes_payloads_with_configured_serializer(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        payload = {"value": [1, 2, 3]}
        serialized = backend._serialize_payload(payload)

        assert isinstance(serialized, bytes)
        assert backend._deserialize_payload(serialized) == payload
        assert backend.serializer_content_type == "application/python-pickle"
    finally:
        backend.close()


def test_disk_cache_backend_wraps_payload_serialization_errors(tmp_path: Path) -> None:
    from useful_decorators import CacheSerializationError

    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        with pytest.raises(CacheSerializationError, match="failed to serialize cache value"):
            backend._serialize_payload(lambda value: value)
    finally:
        backend.close()


class JsonLikeSerializer:
    content_type = "application/x-test-json-like"

    def dumps(self, value: object) -> bytes:
        import json

        return json.dumps(value).encode("utf-8")

    def loads(self, data: bytes) -> object:
        import json

        return json.loads(data.decode("utf-8"))


def test_disk_cache_backend_uses_custom_payload_serializer(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", serializer=JsonLikeSerializer())
    try:
        payload = {"value": [1, 2, 3]}
        serialized = backend._serialize_payload(payload)

        assert serialized == b'{"value": [1, 2, 3]}'
        assert backend._deserialize_payload(serialized) == payload
        assert backend.serializer_content_type == "application/x-test-json-like"
    finally:
        backend.close()


class MutableClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_disk_cache_backend_stores_and_retrieves_values(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        assert backend.get("missing") is None
        backend.set_value("key", {"answer": 42})

        entry = backend.get("key")

        assert entry is not None
        assert entry.payload == {"answer": 42}
        assert entry.is_exception is False
        assert backend.info().hits == 1
        assert backend.info().misses == 1
        assert backend.info().currsize == 1
    finally:
        backend.close()


def test_disk_cache_backend_persists_values_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    first = DiskCacheBackend(db_path)
    first.set_value("key", "persisted")
    first.close()

    second = DiskCacheBackend(db_path)
    try:
        entry = second.get("key")

        assert entry is not None
        assert entry.payload == "persisted"
    finally:
        second.close()


def test_disk_cache_backend_stores_and_retrieves_exceptions(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        backend.set_exception("key", ValueError("boom"))

        entry = backend.get("key")

        assert entry is not None
        assert isinstance(entry.payload, ValueError)
        assert str(entry.payload) == "boom"
        assert entry.is_exception is True
    finally:
        backend.close()


def test_disk_cache_backend_expires_entries(tmp_path: Path) -> None:
    clock = MutableClock()
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", ttl=10, clock=clock)
    try:
        backend.set_value("key", "value")
        clock.advance(11)

        assert backend.get("key") is None
        assert backend.info().currsize == 0
        assert backend.info().misses == 1
    finally:
        backend.close()


def test_disk_cache_backend_evicts_lru_entries(tmp_path: Path) -> None:
    clock = MutableClock()
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", maxsize=2, clock=clock)
    try:
        backend.set_value("a", "A")
        clock.advance(1)
        backend.set_value("b", "B")
        clock.advance(1)
        assert backend.get("a") is not None
        clock.advance(1)
        backend.set_value("c", "C")

        assert backend.get("b") is None
        assert backend.get("a") is not None
        assert backend.get("c") is not None
        assert backend.info().currsize == 2
    finally:
        backend.close()


def test_disk_cache_backend_clear_removes_entries_and_resets_stats(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        backend.set_value("key", "value")
        assert backend.get("key") is not None
        assert backend.get("missing") is None

        backend.clear()

        assert backend.info().hits == 0
        assert backend.info().misses == 0
        assert backend.info().currsize == 0
    finally:
        backend.close()


def test_disk_cache_backend_rejects_operations_after_close(tmp_path: Path) -> None:
    from useful_decorators import CacheBackendClosedError

    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    backend.close()

    with pytest.raises(CacheBackendClosedError, match="cache backend is closed"):
        backend.info()


def test_disk_cache_backend_treats_serializer_content_type_mismatch_as_miss(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    first = DiskCacheBackend(db_path)
    first.set_value("key", {"value": 1})
    first.close()

    second = DiskCacheBackend(db_path, serializer=JsonLikeSerializer())
    try:
        assert second.get("key") is None
        assert second.info().misses == 1
        assert second.info().currsize == 0
    finally:
        second.close()


def test_cache_result_works_with_disk_cache_backend(tmp_path: Path) -> None:
    from useful_decorators import cache_result

    calls = 0
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")

    @cache_result(backend=backend)
    def add_one(value: int) -> int:
        nonlocal calls
        calls += 1
        return value + 1

    try:
        assert add_one(1) == 2
        assert add_one(1) == 2
        assert calls == 1
        assert add_one.cache_info().hits == 1  # type: ignore[attr-defined]
    finally:
        backend.close()
