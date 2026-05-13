import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

import pytest

from useful_decorators import (
    DiskCacheAggregateInspectionReport,
    DiskCacheBackend,
    DiskCacheInspectionReport,
    DiskCachePreviewContext,
    JsonCacheSerializer,
)
from useful_decorators.exceptions import ConfigurationError, UnsupportedCacheSchemaVersionError


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

    with closing(sqlite3.connect(db_path)) as connection:
        [schema_version] = connection.execute("PRAGMA user_version").fetchone()

    assert schema_version == 1


def test_disk_cache_backend_rejects_unsupported_future_schema_version(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute("PRAGMA user_version = 999")

    with pytest.raises(
        UnsupportedCacheSchemaVersionError,
        match="disk cache schema version is newer than this package supports",
    ):
        DiskCacheBackend(db_path)


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


def test_disk_cache_backend_uses_json_payload_serializer(tmp_path: Path) -> None:
    backend = DiskCacheBackend(
        tmp_path / "cache.sqlite3",
        serializer=JsonCacheSerializer(),
    )
    try:
        payload = {"value": [1, 2, 3], "ok": True}
        serialized = backend._serialize_payload(payload)

        assert serialized == b'{"value":[1,2,3],"ok":true}'
        assert backend._deserialize_payload(serialized) == payload
        assert backend.serializer_content_type == "application/json"
    finally:
        backend.close()


def test_disk_cache_backend_persists_json_payloads_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    first = DiskCacheBackend(db_path, serializer=JsonCacheSerializer())
    first.set_value("key", {"answer": 42})
    first.close()

    second = DiskCacheBackend(db_path, serializer=JsonCacheSerializer())
    try:
        entry = second.get("key")

        assert entry is not None
        assert entry.payload == {"answer": 42}
    finally:
        second.close()


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


def test_disk_cache_backend_persists_values_across_subprocesses(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    writer = """
from pathlib import Path
from useful_decorators import DiskCacheBackend
backend = DiskCacheBackend(Path(__CACHE_PATH__))
try:
    backend.set_value('key', 'from-subprocess')
finally:
    backend.close()
""".replace("__CACHE_PATH__", repr(str(db_path)))
    reader = """
from pathlib import Path
from useful_decorators import DiskCacheBackend
backend = DiskCacheBackend(Path(__CACHE_PATH__))
try:
    entry = backend.get('key')
    assert entry is not None
    print(entry.payload)
finally:
    backend.close()
""".replace("__CACHE_PATH__", repr(str(db_path)))

    subprocess.run([sys.executable, "-c", writer], check=True, cwd=Path.cwd())
    result = subprocess.run(
        [sys.executable, "-c", reader],
        check=True,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "from-subprocess"


def test_disk_cache_backend_can_refresh_ttl_on_hit(tmp_path: Path) -> None:
    clock = MutableClock()
    backend = DiskCacheBackend(
        tmp_path / "cache.sqlite3",
        ttl=10,
        refresh_ttl_on_hit=True,
        clock=clock,
    )
    try:
        backend.set_value("key", "value")
        clock.advance(9)
        assert backend.get("key") is not None
        clock.advance(9)
        assert backend.get("key") is not None
        clock.advance(10)
        assert backend.get("key") is None
        assert backend.info().misses == 1
    finally:
        backend.close()


def test_disk_cache_backend_does_not_refresh_ttl_on_hit_by_default(tmp_path: Path) -> None:
    clock = MutableClock()
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", ttl=10, clock=clock)
    try:
        backend.set_value("key", "value")
        clock.advance(9)
        assert backend.get("key") is not None
        clock.advance(1)
        assert backend.get("key") is None
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


def test_disk_cache_backend_reports_serializer_content_type_mismatch_drop(
    tmp_path: Path,
) -> None:
    from useful_decorators import DiskCacheDropEvent

    events: list[DiskCacheDropEvent] = []
    db_path = tmp_path / "cache.sqlite3"
    first = DiskCacheBackend(db_path)
    first.set_value("key", {"value": 1})
    first.close()

    second = DiskCacheBackend(
        db_path,
        serializer=JsonLikeSerializer(),
        on_drop=events.append,
    )
    try:
        assert second.get("key") is None

        assert events == [
            DiskCacheDropEvent(
                key="key",
                reason="serializer_content_type_mismatch",
                expected_serializer_content_type="application/x-test-json-like",
                actual_serializer_content_type="application/python-pickle",
            )
        ]
    finally:
        second.close()


def test_disk_cache_backend_reports_corrupt_payload_drop(tmp_path: Path) -> None:
    from useful_decorators import DiskCacheDropEvent

    events: list[DiskCacheDropEvent] = []
    db_path = tmp_path / "cache.sqlite3"
    backend = DiskCacheBackend(db_path)
    serialized_key = backend._serialize_key("key")
    backend.close()

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute(
            """
            INSERT INTO cache_entries (
                key, payload, is_exception, expires_at, last_accessed, created_at,
                serializer_content_type
            )
            VALUES (?, ?, 0, NULL, 100, 100, ?)
            """,
            (serialized_key, b"not a pickle payload", "application/python-pickle"),
        )
        connection.commit()

    backend = DiskCacheBackend(db_path, on_drop=events.append)
    try:
        assert backend.get("key") is None

        assert len(events) == 1
        [event] = events
        assert event.key == "key"
        assert event.reason == "payload_deserialization_error"
        assert event.expected_serializer_content_type == "application/python-pickle"
        assert event.actual_serializer_content_type == "application/python-pickle"
        assert event.exception is not None
    finally:
        backend.close()


def test_disk_cache_backend_drop_hook_failures_do_not_break_cache_miss(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "cache.sqlite3"
    first = DiskCacheBackend(db_path)
    first.set_value("key", {"value": 1})
    first.close()

    def broken_hook(event: object) -> None:
        raise RuntimeError("diagnostic sink failed")

    second = DiskCacheBackend(
        db_path,
        serializer=JsonLikeSerializer(),
        on_drop=broken_hook,
    )
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


def test_disk_cache_backend_treats_corrupt_payload_as_miss(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    backend = DiskCacheBackend(db_path)
    serialized_key = backend._serialize_key("key")
    backend.close()

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute(
            """
            INSERT INTO cache_entries (
                key, payload, is_exception, expires_at, last_accessed, created_at,
                serializer_content_type
            )
            VALUES (?, ?, 0, NULL, 100, 100, ?)
            """,
            (serialized_key, b"not a pickle payload", "application/python-pickle"),
        )
        connection.commit()

    backend = DiskCacheBackend(db_path)
    try:
        assert backend.get("key") is None
        assert backend.info().misses == 1
        assert backend.info().hits == 0
        assert backend.info().currsize == 0
    finally:
        backend.close()


def test_disk_cache_backend_maintenance_drops_expired_corrupt_and_incompatible_rows(
    tmp_path: Path,
) -> None:
    clock = MutableClock()
    db_path = tmp_path / "cache.sqlite3"
    backend = DiskCacheBackend(db_path, ttl=10, clock=clock)
    corrupt_key = backend._serialize_key("corrupt")
    incompatible_key = backend._serialize_key("incompatible")
    backend.set_value("stale", "old")
    backend.close()
    clock.advance(11)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute(
            """
            INSERT INTO cache_entries (
                key, payload, is_exception, expires_at, last_accessed, created_at,
                serializer_content_type
            )
            VALUES (?, ?, 0, NULL, 100, 100, ?)
            """,
            (corrupt_key, b"not a pickle payload", "application/python-pickle"),
        )
        connection.execute(
            """
            INSERT INTO cache_entries (
                key, payload, is_exception, expires_at, last_accessed, created_at,
                serializer_content_type
            )
            VALUES (?, ?, 0, NULL, 100, 100, ?)
            """,
            (incompatible_key, b"{}", "application/json"),
        )
        connection.commit()

    backend = DiskCacheBackend(db_path, ttl=10, clock=clock)
    try:
        report = backend.maintain()

        assert report.expired_rows_dropped == 1
        assert report.corrupt_rows_dropped == 1
        assert report.serializer_mismatch_rows_dropped == 1
        assert report.vacuumed is False
        assert backend.info().currsize == 0
        assert backend.get("stale") is None
    finally:
        backend.close()


def test_disk_cache_backend_maintenance_can_vacuum(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        report = backend.maintain(vacuum=True)

        assert report.vacuumed is True
    finally:
        backend.close()


def test_disk_cache_backend_inspects_entries_without_raw_keys_or_previews_by_default(
    tmp_path: Path,
) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", serializer=JsonCacheSerializer())
    try:
        backend.set_value("user:1", {"token": "secret", "name": "Ada"})
        report = backend.inspect_entries()

        assert isinstance(report, DiskCacheInspectionReport)
        assert report.total_entries == 1
        assert report.truncated is False
        assert report.mode == "metadata"
        assert "metadata" in report.sensitivity_warning
        [entry] = report.entries
        assert len(entry.key_sha256) == 64
        assert entry.key_sha256 != "user:1"
        assert entry.payload_preview is None
        assert entry.payload_size_bytes > 0
        assert entry.serializer_content_type == "application/json"
        assert entry.created_at == entry.last_accessed
    finally:
        backend.close()


def test_disk_cache_backend_inspection_supports_bounded_redacted_payload_previews(
    tmp_path: Path,
) -> None:
    seen_contexts: list[DiskCachePreviewContext] = []
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", serializer=JsonCacheSerializer())
    try:
        backend.set_value("user:1", {"token": "secret", "name": "Ada"})

        def redact(preview: str, context: DiskCachePreviewContext) -> str:
            seen_contexts.append(context)
            return preview.replace("secret", "<redacted>")

        report = backend.inspect_entries(
            include_payload_preview=True,
            payload_preview_bytes=30,
            preview_redactor=redact,
        )

        [entry] = report.entries
        assert report.mode == "preview"
        assert "payload previews" in report.sensitivity_warning
        assert entry.payload_preview is not None
        assert "<redacted>" in entry.payload_preview
        assert "secret" not in entry.payload_preview
        assert entry.payload_preview.endswith("…")
        assert seen_contexts[0].key_sha256 == entry.key_sha256
        assert seen_contexts[0].payload_size_bytes == entry.payload_size_bytes
    finally:
        backend.close()


def test_disk_cache_backend_inspection_tracks_redaction_failures(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", serializer=JsonCacheSerializer())
    try:
        backend.set_value("user:1", {"token": "secret"})

        def broken_redactor(preview: str, context: DiskCachePreviewContext) -> str:
            raise RuntimeError("redactor failed")

        report = backend.inspect_entries(
            include_payload_preview=True,
            preview_redactor=broken_redactor,
        )

        assert report.preview_redaction_failures == 1
        assert report.entries[0].payload_preview is None
    finally:
        backend.close()


def test_disk_cache_backend_inspection_safe_mode_does_not_call_redactor(tmp_path: Path) -> None:
    called = False
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", serializer=JsonCacheSerializer())
    try:
        backend.set_value("user:1", {"token": "secret"})

        def redactor(preview: str, context: DiskCachePreviewContext) -> str:
            nonlocal called
            called = True
            return preview

        report = backend.inspect_entries(preview_redactor=redactor)

        assert report.mode == "metadata"
        assert report.entries[0].payload_preview is None
        assert called is False
    finally:
        backend.close()


def test_disk_cache_backend_inspection_enforces_limits_and_reports_truncation(
    tmp_path: Path,
) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        backend.set_value("first", "one")
        backend.set_value("second", "two")

        report = backend.inspect_entries(limit=1)

        assert report.total_entries == 2
        assert report.truncated is True
        assert len(report.entries) == 1
        with pytest.raises(ConfigurationError, match="limit must be a positive integer"):
            backend.inspect_entries(limit=0)
        with pytest.raises(ConfigurationError, match="payload_preview_bytes must be between"):
            backend.inspect_entries(payload_preview_bytes=4097)
        with pytest.raises(ConfigurationError, match="preview_redactor must be callable"):
            backend.inspect_entries(preview_redactor=object())  # type: ignore[arg-type]
    finally:
        backend.close()


def test_disk_cache_backend_aggregate_inspection_omits_row_level_sensitive_data(
    tmp_path: Path,
) -> None:
    clock = MutableClock()
    backend = DiskCacheBackend(
        tmp_path / "cache.sqlite3",
        ttl=10,
        clock=clock,
    )
    try:
        backend.set_value("user:1", {"token": "secret"})
        backend.set_exception("user:2", RuntimeError("boom"))
        clock.advance(11)

        hits_before, misses_before = backend._connection.execute(
            "SELECT hits, misses FROM cache_stats WHERE id = 1"
        ).fetchone()
        report = backend.inspect_aggregate()
        hits_after, misses_after = backend._connection.execute(
            "SELECT hits, misses FROM cache_stats WHERE id = 1"
        ).fetchone()

        assert isinstance(report, DiskCacheAggregateInspectionReport)
        assert report.total_entries == 2
        assert report.scanned_entries == 2
        assert report.value_entries == 1
        assert report.exception_entries == 1
        assert report.expired_entries == 2
        assert report.serializer_content_types == {"application/python-pickle": 2}
        assert report.total_payload_bytes > 0
        assert report.largest_payload_bytes is not None
        assert report.truncated is False
        assert report.mode == "aggregate"
        assert "payload previews" in report.sensitivity_warning
        assert "key digests" in report.sensitivity_warning
        assert (hits_before, misses_before) == (hits_after, misses_after)
        assert not hasattr(report, "entries")
    finally:
        backend.close()


def test_disk_cache_backend_aggregate_inspection_reports_truncation_and_validates_limit(
    tmp_path: Path,
) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    try:
        backend.set_value("first", "one")
        backend.set_value("second", "two")

        report = backend.inspect_aggregate(limit=1)

        assert report.total_entries == 2
        assert report.scanned_entries == 1
        assert report.truncated is True
        with pytest.raises(ConfigurationError, match="limit must be a positive integer"):
            backend.inspect_aggregate(limit=0)
    finally:
        backend.close()


def test_disk_cache_backend_configures_sqlite_operational_pragmas(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite3"
    backend = DiskCacheBackend(db_path, busy_timeout_ms=7_500)
    try:
        assert backend.busy_timeout_ms == 7_500
        assert backend.wal_enabled is True
        busy_timeout = backend._connection.execute("PRAGMA busy_timeout").fetchone()[0]
        journal_mode = backend._connection.execute("PRAGMA journal_mode").fetchone()[0]

        assert busy_timeout == 7_500
        assert journal_mode.lower() == "wal"
    finally:
        backend.close()


def test_disk_cache_backend_allows_disabling_wal(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", wal=False)
    try:
        journal_mode = backend._connection.execute("PRAGMA journal_mode").fetchone()[0]

        assert backend.wal_enabled is False
        assert journal_mode.lower() != "wal"
    finally:
        backend.close()


def test_disk_cache_backend_rejects_negative_busy_timeout(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="busy_timeout_ms must be zero or greater"):
        DiskCacheBackend(tmp_path / "cache.sqlite3", busy_timeout_ms=-1)


def test_decorator_bound_disk_backend_fails_after_context_manager_exit(tmp_path: Path) -> None:
    from useful_decorators import CacheBackendClosedError, cache_result

    with DiskCacheBackend(tmp_path / "cache.sqlite3") as backend:

        @cache_result(backend=backend)
        def add_one(value: int) -> int:
            return value + 1

        assert add_one(1) == 2

    with pytest.raises(CacheBackendClosedError, match="cache backend is closed"):
        add_one(1)


def test_disk_cache_backend_smoke_concurrent_reads_and_writes(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3", maxsize=128)

    def write_then_read(index: int) -> int:
        key = f"key-{index % 8}"
        backend.set_value(key, index)
        entry = backend.get(key)
        assert entry is not None
        assert isinstance(entry.payload, int)
        return entry.payload

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(write_then_read, range(64)))

        assert len(results) == 64
        info = backend.info()
        assert info.hits == 64
        assert info.currsize <= 8
    finally:
        backend.close()
