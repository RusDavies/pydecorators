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


def closed_backend_error_example(cache_path: Path) -> str:
    """Handle CacheBackendClosedError from a closed disk backend."""

    from useful_decorators import CacheBackendClosedError

    backend = DiskCacheBackend(cache_path)
    backend.close()

    try:
        backend.info()
    except CacheBackendClosedError:
        return "closed"
    return "open"


def persistent_disk_cache_example(cache_path: Path) -> tuple[str, str, int]:
    """Show cached values surviving a new DiskCacheBackend instance."""

    global _CALLS
    _CALLS = 0

    first_backend = DiskCacheBackend(cache_path, ttl=3600, maxsize=10_000)

    @cache_result(backend=first_backend, namespace="persistent-users")
    def load_user_display_name_first(user_id: str) -> str:
        return fetch_user_display_name(user_id)

    try:
        first = load_user_display_name_first("user-456")
    finally:
        first_backend.close()

    second_backend = DiskCacheBackend(cache_path, ttl=3600, maxsize=10_000)

    @cache_result(backend=second_backend, namespace="persistent-users")
    def load_user_display_name_second(user_id: str) -> str:
        return fetch_user_display_name(user_id)

    try:
        second = load_user_display_name_second("user-456")
        return first, second, _CALLS
    finally:
        second_backend.close()


class DateTimeBytesJsonSerializer:
    """Example JSON serializer that adapts datetimes and bytes explicitly."""

    content_type = "application/json+datetime-bytes-example"

    def dumps(self, value: object) -> bytes:
        """Serialize a JSON-like value after adapting datetime and bytes values."""

        import base64
        import json
        from datetime import datetime

        from useful_decorators import CacheSerializationError

        def encode(item: object) -> object:
            if isinstance(item, datetime):
                return {"__type__": "datetime", "value": item.isoformat()}
            if isinstance(item, bytes):
                return {
                    "__type__": "bytes",
                    "value": base64.b64encode(item).decode("ascii"),
                }
            if isinstance(item, list):
                return [encode(value) for value in item]
            if isinstance(item, dict):
                return {key: encode(value) for key, value in item.items()}
            return item

        try:
            return json.dumps(
                encode(value),
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise CacheSerializationError("failed to serialize cache value") from exc

    def loads(self, data: bytes) -> object:
        """Deserialize JSON bytes and restore adapted datetime and bytes values."""

        import base64
        import json
        from datetime import datetime

        from useful_decorators import CacheSerializationError

        def decode(item: object) -> object:
            if isinstance(item, list):
                return [decode(value) for value in item]
            if isinstance(item, dict):
                if item.get("__type__") == "datetime":
                    return datetime.fromisoformat(str(item["value"]))
                if item.get("__type__") == "bytes":
                    return base64.b64decode(str(item["value"]).encode("ascii"))
                return {key: decode(value) for key, value in item.items()}
            return item

        try:
            return decode(json.loads(data.decode("utf-8")))
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CacheSerializationError("failed to deserialize cache value") from exc


def json_datetime_bytes_serializer_example(cache_path: Path) -> tuple[object, object]:
    """Use a custom JSON serializer for datetime and bytes payload values."""

    from datetime import UTC, datetime

    backend = DiskCacheBackend(
        cache_path,
        serializer=DateTimeBytesJsonSerializer(),
    )
    payload = {
        "created_at": datetime(2026, 5, 11, 12, 30, tzinfo=UTC),
        "digest": b"abc123",
    }
    try:
        backend.set_value("artifact", payload)
        entry = backend.get("artifact")
        assert entry is not None
        restored = entry.payload
        assert isinstance(restored, dict)
        return restored["created_at"], restored["digest"]
    finally:
        backend.close()
