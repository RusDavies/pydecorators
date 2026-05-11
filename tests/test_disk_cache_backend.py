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
