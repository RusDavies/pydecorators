"""In-memory result caching decorator."""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import sqlite3
import sys
from collections import OrderedDict
from collections.abc import Callable, Hashable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import Event, RLock
from typing import Any, Protocol, cast, runtime_checkable

from pydecorators._core import is_async_callable, mirror_metadata, monotonic
from pydecorators._typing import Clock, P, R
from pydecorators.exceptions import (
    CacheBackendClosedError,
    CacheKeyError,
    CacheSerializationError,
    ConfigurationError,
    UnsupportedCacheSchemaVersionError,
)

_KW_MARKER = object()
_TYPE_MARKER = object()
_DISK_CACHE_SCHEMA_VERSION = 1
_MAX_PAYLOAD_PREVIEW_BYTES = 4096


@dataclass(frozen=True, slots=True)
class CacheInfo:
    """Cache statistics exposed by ``cache_info()`` on cached functions."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int


@dataclass(frozen=True, slots=True)
class CacheCoalescingInfo:
    """Duplicate-miss coalescing diagnostics exposed by cached functions."""

    current_in_flight: int
    total_waiters: int
    total_wait_seconds: float


@dataclass(frozen=True, slots=True)
class DiskCacheDropEvent:
    """Diagnostic event for a disk-cache row dropped during lookup."""

    key: Hashable
    reason: str
    expected_serializer_content_type: str
    actual_serializer_content_type: str | None = None
    exception: BaseException | None = None


@dataclass(frozen=True, slots=True)
class DiskCacheMetadata:
    """Stable disk-cache file metadata for diagnostics and compatibility checks."""

    path: Path
    schema_version: int
    serializer_content_type: str
    busy_timeout_ms: int
    wal_enabled: bool


@dataclass(frozen=True, slots=True)
class DiskCacheIntegrityReport:
    """Read-only count of rows that maintenance would drop."""

    total_entries: int
    expired_rows: int
    corrupt_rows: int
    serializer_mismatch_rows: int
    sensitivity_warning: str = "Cache integrity reports may expose operational metadata."


@dataclass(frozen=True, slots=True)
class DiskCacheMaintenanceReport:
    """Summary returned by ``DiskCacheBackend.maintain()``."""

    expired_rows_dropped: int
    corrupt_rows_dropped: int
    serializer_mismatch_rows_dropped: int
    vacuumed: bool = False


@dataclass(frozen=True, slots=True)
class DiskCachePreviewContext:
    """Context passed to disk-cache payload preview redactors."""

    key_sha256: str
    serializer_content_type: str
    is_exception: bool
    payload_size_bytes: int


@dataclass(frozen=True, slots=True)
class DiskCacheInspectionEntry:
    """Read-only diagnostic entry returned by ``DiskCacheBackend.inspect_entries()``."""

    key_sha256: str
    is_exception: bool
    serializer_content_type: str
    payload_preview: str | None
    payload_size_bytes: int
    created_at: float
    last_accessed: float
    expires_at: float | None


@dataclass(frozen=True, slots=True)
class DiskCacheInspectionReport:
    """Read-only diagnostic report returned by ``DiskCacheBackend.inspect_entries()``."""

    entries: tuple[DiskCacheInspectionEntry, ...]
    total_entries: int
    truncated: bool
    preview_redaction_failures: int = 0
    sensitivity_warning: str = "Cache inspection reports may expose sensitive metadata."
    created_at: float = 0.0
    mode: str = "metadata"


@dataclass(frozen=True, slots=True)
class DiskCacheAggregateInspectionReport:
    """Aggregate read-only diagnostics for support bundles and broad sharing."""

    total_entries: int
    value_entries: int
    exception_entries: int
    expired_entries: int
    serializer_content_types: dict[str, int]
    total_payload_bytes: int
    largest_payload_bytes: int | None
    scanned_entries: int
    truncated: bool
    sensitivity_warning: str
    created_at: float
    mode: str = "aggregate"


PreviewRedactor = Callable[[str, DiskCachePreviewContext], str]


@dataclass(slots=True)
class _CacheEntry:
    """Internal cache entry for values or cached exceptions."""

    payload: Any
    expires_at: float | None
    is_exception: bool = False


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol implemented by cache storage backends."""

    def get(self, key: Hashable) -> _CacheEntry | None:
        """Return a cached entry for *key*, or ``None`` for a miss."""

    def set_value(self, key: Hashable, value: object) -> None:
        """Store a successful cached value."""

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        """Store an exception payload for later re-raising."""

    def clear(self) -> None:
        """Clear cached entries and reset statistics where supported."""

    def info(self) -> CacheInfo:
        """Return cache statistics."""


@runtime_checkable
class CacheSerializer(Protocol):
    """Protocol for serializing cache payloads for persistent backends."""

    content_type: str

    def dumps(self, value: object) -> bytes:
        """Serialize *value* to bytes."""

    def loads(self, data: bytes) -> object:
        """Deserialize bytes back to a Python object."""


class PickleCacheSerializer:
    """Default serializer for Python-object cache payloads.

    Pickle is convenient for local trusted caches, but it is not safe for
    untrusted data. Persistent/distributed backends must document that warning
    loudly enough that even a hurried monkey notices.
    """

    content_type = "application/python-pickle"

    def __init__(self, *, protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
        self._protocol = protocol

    def dumps(self, value: object) -> bytes:
        """Serialize *value* with pickle."""

        try:
            return pickle.dumps(value, protocol=self._protocol)
        except Exception as exc:
            raise CacheSerializationError("failed to serialize cache value") from exc

    def loads(self, data: bytes) -> object:
        """Deserialize pickle bytes."""

        try:
            return pickle.loads(data)
        except Exception as exc:
            raise CacheSerializationError("failed to deserialize cache value") from exc


class JsonCacheSerializer:
    """JSON serializer for simple cross-language cache payloads.

    This serializer is intended for JSON-compatible values such as ``None``,
    booleans, numbers, strings, lists, and dictionaries with string keys. It is
    less Python-specific than pickle, but it does not preserve arbitrary Python
    object types.
    """

    content_type = "application/json"

    def dumps(self, value: object) -> bytes:
        """Serialize a JSON-compatible value to UTF-8 JSON bytes."""

        try:
            return json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise CacheSerializationError("failed to serialize cache value") from exc

    def loads(self, data: bytes) -> object:
        """Deserialize UTF-8 JSON bytes."""

        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CacheSerializationError("failed to deserialize cache value") from exc


class MemoryCacheBackend:
    """Thread-safe in-memory cache backend used by ``@cache_result``.

    This backend owns storage, TTL pruning, LRU eviction, and hit/miss
    statistics. The decorator remains responsible for key generation and for
    executing wrapped functions outside backend locks.
    """

    def __init__(
        self,
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        refresh_ttl_on_hit: bool = False,
        clock: Clock | None = None,
    ) -> None:
        if ttl is not None and ttl <= 0:
            raise ConfigurationError("ttl must be greater than zero when provided")
        if maxsize is not None and maxsize <= 0:
            raise ConfigurationError("maxsize must be greater than zero when provided")

        self._ttl = ttl
        self._maxsize = maxsize
        self._refresh_ttl_on_hit = refresh_ttl_on_hit
        self._clock = clock or monotonic
        self._lock = RLock()
        self._cache: OrderedDict[Hashable, _CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: Hashable) -> _CacheEntry | None:
        """Return a cache entry for *key*, or ``None`` after recording a miss."""

        with self._lock:
            entry = self._cache.get(key)
            if entry is not None:
                if self._is_expired(entry):
                    self._cache.pop(key, None)
                else:
                    self._hits += 1
                    if self._refresh_ttl_on_hit:
                        entry.expires_at = self._expires_at()
                    self._cache.move_to_end(key)
                    return entry
            self._misses += 1
            return None

    def set_value(self, key: Hashable, value: object) -> None:
        """Store a successful cached value."""

        self._set_entry(key, _CacheEntry(value, expires_at=self._expires_at()))

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        """Store an exception payload for later re-raising."""

        self._set_entry(
            key,
            _CacheEntry(exception, expires_at=self._expires_at(), is_exception=True),
        )

    def clear(self) -> None:
        """Clear cached entries and reset statistics."""

        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def info(self) -> CacheInfo:
        """Return current cache statistics after pruning expired entries."""

        with self._lock:
            self._prune_expired()
            return CacheInfo(
                hits=self._hits,
                misses=self._misses,
                maxsize=self._maxsize,
                currsize=len(self._cache),
            )

    def _set_entry(self, key: Hashable, entry: _CacheEntry) -> None:
        with self._lock:
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._evict_if_needed()

    def _is_expired(self, entry: _CacheEntry) -> bool:
        return entry.expires_at is not None and self._clock() >= entry.expires_at

    def _expires_at(self) -> float | None:
        if self._ttl is None:
            return None
        return self._clock() + self._ttl

    def _evict_if_needed(self) -> None:
        if self._maxsize is None:
            return
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def _prune_expired(self) -> None:
        expired_keys = [key for key, entry in self._cache.items() if self._is_expired(entry)]
        for expired_key in expired_keys:
            self._cache.pop(expired_key, None)


class DiskCacheBackend:
    """SQLite-backed local persistent cache backend."""

    def __init__(
        self,
        path: str | Path,
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        refresh_ttl_on_hit: bool = False,
        serializer: CacheSerializer | None = None,
        on_drop: Callable[[DiskCacheDropEvent], object] | None = None,
        clock: Clock | None = None,
        busy_timeout_ms: int = 5_000,
        wal: bool = True,
        drop_corrupt_rows: bool = True,
    ) -> None:
        if ttl is not None and ttl <= 0:
            raise ConfigurationError("ttl must be greater than zero when provided")
        if maxsize is not None and maxsize <= 0:
            raise ConfigurationError("maxsize must be greater than zero when provided")
        if busy_timeout_ms < 0:
            raise ConfigurationError("busy_timeout_ms must be zero or greater")

        self.path = Path(path)
        self._ttl = ttl
        self._maxsize = maxsize
        self._refresh_ttl_on_hit = refresh_ttl_on_hit
        self._key_serializer = PickleCacheSerializer()
        self._serializer = serializer or PickleCacheSerializer()
        self._on_drop = on_drop
        self._clock = clock or monotonic
        self._busy_timeout_ms = busy_timeout_ms
        self._wal = wal
        self._drop_corrupt_rows = drop_corrupt_rows
        self._lock = RLock()
        self._closed = False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
            timeout=busy_timeout_ms / 1000,
        )
        self._configure_connection()
        self._check_schema_version()
        self._initialize_schema()

    def _configure_connection(self) -> None:
        with self._lock:
            self._connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
            if self._wal:
                self._connection.execute("PRAGMA journal_mode = WAL")

    @property
    def busy_timeout_ms(self) -> int:
        """Return the SQLite busy timeout configured for this backend."""

        return self._busy_timeout_ms

    @property
    def wal_enabled(self) -> bool:
        """Return whether this backend requests SQLite WAL journal mode."""

        return self._wal

    def __enter__(self) -> DiskCacheBackend:
        """Return this backend for context-manager usage."""

        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Close the SQLite connection when leaving a context manager."""

        self.close()

    def __del__(self) -> None:
        """Best-effort connection cleanup for forgotten backend instances."""

        with suppress(Exception):
            self.close()

    def close(self) -> None:
        """Close the underlying SQLite connection."""

        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True

    def get(self, key: Hashable) -> _CacheEntry | None:
        """Return a cached entry for *key*, or ``None`` after recording a miss."""

        serialized_key = self._serialize_key(key)
        now = self._clock()
        with self._lock:
            self._ensure_open()
            with self._connection:
                row = self._connection.execute(
                    """
                SELECT payload, is_exception, expires_at, serializer_content_type
                FROM cache_entries
                WHERE key = ?
                """,
                    (serialized_key,),
                ).fetchone()
                if row is None:
                    self._record_miss()
                    return None

                payload, is_exception, expires_at, serializer_content_type = row
                if expires_at is not None and now >= expires_at:
                    self._connection.execute(
                        "DELETE FROM cache_entries WHERE key = ?", (serialized_key,)
                    )
                    self._record_miss()
                    return None

                if serializer_content_type != self.serializer_content_type:
                    self._connection.execute(
                        "DELETE FROM cache_entries WHERE key = ?", (serialized_key,)
                    )
                    self._report_dropped_row(
                        key,
                        reason="serializer_content_type_mismatch",
                        actual_serializer_content_type=serializer_content_type,
                    )
                    self._record_miss()
                    return None

                try:
                    deserialized_payload = self._deserialize_payload(payload)
                except CacheSerializationError as exc:
                    if not self._drop_corrupt_rows:
                        raise
                    self._connection.execute(
                        "DELETE FROM cache_entries WHERE key = ?", (serialized_key,)
                    )
                    self._report_dropped_row(
                        key,
                        reason="payload_deserialization_error",
                        actual_serializer_content_type=serializer_content_type,
                        exception=exc,
                    )
                    self._record_miss()
                    return None

                refreshed_expires_at = (
                    self._expires_at(now) if self._refresh_ttl_on_hit else expires_at
                )
                self._connection.execute(
                    """
                    UPDATE cache_entries
                    SET last_accessed = ?, expires_at = ?
                    WHERE key = ?
                    """,
                    (now, refreshed_expires_at, serialized_key),
                )
                self._record_hit()
                return _CacheEntry(
                    deserialized_payload,
                    expires_at=refreshed_expires_at,
                    is_exception=bool(is_exception),
                )

    def set_value(self, key: Hashable, value: object) -> None:
        """Store a successful cached value."""

        self._set_entry(key, value, is_exception=False)

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        """Store an exception payload for later re-raising."""

        self._set_entry(key, exception, is_exception=True)

    def clear(self) -> None:
        """Clear cached entries and reset statistics."""

        with self._lock:
            self._ensure_open()
            with self._connection:
                self._connection.execute("DELETE FROM cache_entries")
                self._connection.execute("UPDATE cache_stats SET hits = 0, misses = 0 WHERE id = 1")

    def cache_metadata(self) -> DiskCacheMetadata:
        """Return stable disk-cache file metadata for compatibility diagnostics."""

        with self._lock:
            self._ensure_open()
            [schema_version] = self._connection.execute("PRAGMA user_version").fetchone()
            return DiskCacheMetadata(
                path=self.path,
                schema_version=schema_version,
                serializer_content_type=self.serializer_content_type,
                busy_timeout_ms=self._busy_timeout_ms,
                wal_enabled=self._wal,
            )

    def inspect_integrity(self) -> DiskCacheIntegrityReport:
        """Count expired/corrupt/incompatible rows without mutating the cache."""

        now = self._clock()
        with self._lock:
            self._ensure_open()
            rows = self._connection.execute(
                """
                SELECT payload, expires_at, serializer_content_type
                FROM cache_entries
                """
            ).fetchall()

        expired_rows = 0
        corrupt_rows = 0
        serializer_mismatch_rows = 0
        for payload, expires_at, serializer_content_type in rows:
            if expires_at is not None and now >= expires_at:
                expired_rows += 1
            if serializer_content_type != self.serializer_content_type:
                serializer_mismatch_rows += 1
                continue
            if self._payload_is_corrupt(payload):
                corrupt_rows += 1

        return DiskCacheIntegrityReport(
            total_entries=len(rows),
            expired_rows=expired_rows,
            corrupt_rows=corrupt_rows,
            serializer_mismatch_rows=serializer_mismatch_rows,
        )

    def maintain(self, *, vacuum: bool = False) -> DiskCacheMaintenanceReport:
        """Drop expired/corrupt/incompatible rows and optionally run SQLite VACUUM."""

        now = self._clock()
        with self._lock:
            self._ensure_open()
            with self._connection:
                expired_rows_dropped = self._delete_matching_rows(
                    "expires_at IS NOT NULL AND expires_at <= ?",
                    (now,),
                )
                serializer_mismatch_rows_dropped = self._delete_matching_rows(
                    "serializer_content_type != ?",
                    (self.serializer_content_type,),
                )
                corrupt_keys = [
                    key
                    for key, payload in self._connection.execute(
                        """
                        SELECT key, payload
                        FROM cache_entries
                        WHERE serializer_content_type = ?
                        """,
                        (self.serializer_content_type,),
                    ).fetchall()
                    if self._payload_is_corrupt(payload)
                ]
                corrupt_rows_dropped = 0
                for key in corrupt_keys:
                    cursor = self._connection.execute(
                        "DELETE FROM cache_entries WHERE key = ?",
                        (key,),
                    )
                    corrupt_rows_dropped += cursor.rowcount
            if vacuum:
                self._connection.execute("VACUUM")
            return DiskCacheMaintenanceReport(
                expired_rows_dropped=expired_rows_dropped,
                corrupt_rows_dropped=corrupt_rows_dropped,
                serializer_mismatch_rows_dropped=serializer_mismatch_rows_dropped,
                vacuumed=vacuum,
            )

    def inspect_entries(
        self,
        *,
        limit: int = 100,
        include_payload_preview: bool = False,
        payload_preview_bytes: int = 512,
        preview_redactor: PreviewRedactor | None = None,
    ) -> DiskCacheInspectionReport:
        """Return read-only diagnostics for cache rows without exposing raw keys."""

        if limit < 1:
            raise ConfigurationError("limit must be a positive integer")
        if payload_preview_bytes < 0 or payload_preview_bytes > _MAX_PAYLOAD_PREVIEW_BYTES:
            raise ConfigurationError(
                f"payload_preview_bytes must be between 0 and {_MAX_PAYLOAD_PREVIEW_BYTES}"
            )
        if preview_redactor is not None and not callable(preview_redactor):
            raise ConfigurationError("preview_redactor must be callable when provided")

        with self._lock:
            self._ensure_open()
            rows = self._connection.execute(
                """
                SELECT key, payload, is_exception, serializer_content_type,
                       created_at, last_accessed, expires_at
                FROM cache_entries
                ORDER BY last_accessed DESC, created_at DESC
                LIMIT ?
                """,
                (limit + 1,),
            ).fetchall()
            [total_entries] = self._connection.execute(
                "SELECT COUNT(*) FROM cache_entries"
            ).fetchone()

        redaction_failures = 0
        entries: list[DiskCacheInspectionEntry] = []
        for row in rows[:limit]:
            (
                key,
                payload,
                is_exception,
                serializer_content_type,
                created_at,
                last_accessed,
                expires_at,
            ) = row
            key_sha256 = hashlib.sha256(bytes(key)).hexdigest()
            payload_size_bytes = len(payload)
            payload_preview: str | None = None
            if include_payload_preview:
                payload_preview = _payload_preview(payload, payload_preview_bytes)
                if preview_redactor is not None:
                    context = DiskCachePreviewContext(
                        key_sha256=key_sha256,
                        serializer_content_type=serializer_content_type,
                        is_exception=bool(is_exception),
                        payload_size_bytes=payload_size_bytes,
                    )
                    try:
                        payload_preview = preview_redactor(payload_preview, context)
                    except Exception:
                        redaction_failures += 1
                        payload_preview = None
            entries.append(
                DiskCacheInspectionEntry(
                    key_sha256=key_sha256,
                    is_exception=bool(is_exception),
                    serializer_content_type=serializer_content_type,
                    payload_preview=payload_preview,
                    payload_size_bytes=payload_size_bytes,
                    created_at=created_at,
                    last_accessed=last_accessed,
                    expires_at=expires_at,
                )
            )

        return DiskCacheInspectionReport(
            entries=tuple(entries),
            total_entries=total_entries,
            truncated=len(rows) > limit,
            preview_redaction_failures=redaction_failures,
            created_at=self._clock(),
            mode="preview" if include_payload_preview else "metadata",
            sensitivity_warning=(
                "Cache inspection reports may expose sensitive cached metadata "
                "and payload previews."
                if include_payload_preview
                else "Cache inspection reports may expose sensitive cached metadata."
            ),
        )

    def inspect_aggregate(self, *, limit: int = 10_000) -> DiskCacheAggregateInspectionReport:
        """Return aggregate cache diagnostics without per-row identifiers or previews."""

        if limit < 1:
            raise ConfigurationError("limit must be a positive integer")

        now = self._clock()
        with self._lock:
            self._ensure_open()
            rows = self._connection.execute(
                """
                SELECT payload, is_exception, expires_at, serializer_content_type
                FROM cache_entries
                LIMIT ?
                """,
                (limit + 1,),
            ).fetchall()
            [total_entries] = self._connection.execute(
                "SELECT COUNT(*) FROM cache_entries"
            ).fetchone()

        scanned_rows = rows[:limit]
        serializer_content_types: dict[str, int] = {}
        value_entries = 0
        exception_entries = 0
        expired_entries = 0
        total_payload_bytes = 0
        largest_payload_bytes: int | None = None

        for payload, is_exception, expires_at, serializer_content_type in scanned_rows:
            if is_exception:
                exception_entries += 1
            else:
                value_entries += 1
            if expires_at is not None and now >= expires_at:
                expired_entries += 1
            serializer_content_types[serializer_content_type] = (
                serializer_content_types.get(serializer_content_type, 0) + 1
            )
            payload_size = len(payload)
            total_payload_bytes += payload_size
            largest_payload_bytes = (
                payload_size
                if largest_payload_bytes is None
                else max(largest_payload_bytes, payload_size)
            )

        return DiskCacheAggregateInspectionReport(
            total_entries=total_entries,
            value_entries=value_entries,
            exception_entries=exception_entries,
            expired_entries=expired_entries,
            serializer_content_types=serializer_content_types,
            total_payload_bytes=total_payload_bytes,
            largest_payload_bytes=largest_payload_bytes,
            scanned_entries=len(scanned_rows),
            truncated=len(rows) > limit,
            created_at=now,
            sensitivity_warning=(
                "Aggregate cache inspection reports may expose sensitive operational metadata; "
                "they omit payload previews, raw payload bytes, serialized keys, key digests, "
                "and per-row timestamps."
            ),
        )

    def info(self) -> CacheInfo:
        """Return current cache statistics after pruning expired entries."""

        with self._lock:
            self._ensure_open()
            with self._connection:
                self._prune_expired()
                hits, misses = self._connection.execute(
                    "SELECT hits, misses FROM cache_stats WHERE id = 1"
                ).fetchone()
                currsize = self._connection.execute(
                    "SELECT COUNT(*) FROM cache_entries"
                ).fetchone()[0]
                return CacheInfo(
                    hits=hits,
                    misses=misses,
                    maxsize=self._maxsize,
                    currsize=currsize,
                )

    def _set_entry(self, key: Hashable, payload: object, *, is_exception: bool) -> None:
        serialized_key = self._serialize_key(key)
        serialized_payload = self._serialize_payload(payload)
        now = self._clock()
        with self._lock:
            self._ensure_open()
            with self._connection:
                self._connection.execute(
                    """
                INSERT OR REPLACE INTO cache_entries (
                    key, payload, is_exception, expires_at, last_accessed, created_at,
                    serializer_content_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        serialized_key,
                        serialized_payload,
                        int(is_exception),
                        self._expires_at(now),
                        now,
                        now,
                        self.serializer_content_type,
                    ),
                )
                self._evict_if_needed()

    def _expires_at(self, now: float) -> float | None:
        if self._ttl is None:
            return None
        return now + self._ttl

    def _ensure_open(self) -> None:
        if self._closed:
            raise CacheBackendClosedError("cache backend is closed")

    def _record_hit(self) -> None:
        self._connection.execute("UPDATE cache_stats SET hits = hits + 1 WHERE id = 1")

    def _report_dropped_row(
        self,
        key: Hashable,
        *,
        reason: str,
        actual_serializer_content_type: str | None = None,
        exception: BaseException | None = None,
    ) -> None:
        if self._on_drop is None:
            return
        event = DiskCacheDropEvent(
            key=key,
            reason=reason,
            expected_serializer_content_type=self.serializer_content_type,
            actual_serializer_content_type=actual_serializer_content_type,
            exception=exception,
        )
        with suppress(Exception):
            self._on_drop(event)

    def _record_miss(self) -> None:
        self._connection.execute("UPDATE cache_stats SET misses = misses + 1 WHERE id = 1")

    def _delete_matching_rows(self, where_clause: str, parameters: tuple[object, ...]) -> int:
        cursor = self._connection.execute(
            f"DELETE FROM cache_entries WHERE {where_clause}",
            parameters,
        )
        return cursor.rowcount

    def _payload_is_corrupt(self, payload: bytes) -> bool:
        try:
            self._deserialize_payload(payload)
        except CacheSerializationError:
            return True
        return False

    def _prune_expired(self) -> None:
        now = self._clock()
        self._connection.execute(
            "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now,),
        )

    def _evict_if_needed(self) -> None:
        if self._maxsize is None:
            return
        overflow = (
            self._connection.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
            - self._maxsize
        )
        if overflow <= 0:
            return
        self._connection.execute(
            """
            DELETE FROM cache_entries
            WHERE key IN (
                SELECT key
                FROM cache_entries
                ORDER BY last_accessed ASC, created_at ASC
                LIMIT ?
            )
            """,
            (overflow,),
        )

    def _serialize_key(self, key: Hashable) -> bytes:
        """Serialize a cache key for SQLite storage."""

        return self._key_serializer.dumps(key)

    def _serialize_payload(self, value: object) -> bytes:
        """Serialize a cached value or exception payload."""

        return self._serializer.dumps(value)

    def _deserialize_payload(self, data: bytes) -> object:
        """Deserialize a cached value or exception payload."""

        return self._serializer.loads(data)

    @property
    def serializer_content_type(self) -> str:
        """Return the configured payload serializer content type."""

        return self._serializer.content_type

    def _check_schema_version(self) -> None:
        with self._lock:
            [schema_version] = self._connection.execute("PRAGMA user_version").fetchone()
            if schema_version > _DISK_CACHE_SCHEMA_VERSION:
                raise UnsupportedCacheSchemaVersionError(
                    "disk cache schema version is newer than this package supports"
                )

    def _initialize_schema(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key BLOB PRIMARY KEY,
                    payload BLOB NOT NULL,
                    is_exception INTEGER NOT NULL,
                    expires_at REAL,
                    last_accessed REAL NOT NULL,
                    created_at REAL NOT NULL,
                    serializer_content_type TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    hits INTEGER NOT NULL,
                    misses INTEGER NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                INSERT OR IGNORE INTO cache_stats (id, hits, misses)
                VALUES (1, 0, 0)
                """
            )
            self._connection.execute(f"PRAGMA user_version = {_DISK_CACHE_SCHEMA_VERSION}")


def _payload_preview(payload: bytes, limit: int) -> str:
    preview = payload[:limit]
    suffix = "…" if len(payload) > limit else ""
    return preview.decode("utf-8", errors="replace") + suffix


def redact_json_preview(
    preview: str,
    context: DiskCachePreviewContext | None = None,
    *,
    sensitive_keys: frozenset[str] = frozenset(
        {"api_key", "authorization", "password", "secret", "token"}
    ),
) -> str:
    """Redact obvious sensitive keys from a JSON payload preview."""

    suffix = "…" if preview.endswith("…") else ""
    candidate = preview.removesuffix("…")
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return preview

    def redact(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: "<redacted>" if str(key).lower() in sensitive_keys else redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    return json.dumps(redact(payload), ensure_ascii=False, separators=(",", ":")) + suffix


def _ensure_hashable(value: object) -> Hashable:
    try:
        hash(value)
    except TypeError as exc:
        raise CacheKeyError("cache key must be hashable") from exc
    return value


def cache_namespace(name: str, version: int | str) -> str:
    """Return a conventional versioned cache namespace such as ``users:v1``."""

    normalized_name = name.strip()
    if not normalized_name:
        raise ConfigurationError("cache namespace name must not be empty")
    if ":" in normalized_name:
        raise ConfigurationError("cache namespace name must not contain ':'")
    if isinstance(version, int):
        if version < 1:
            raise ConfigurationError("cache namespace version must be positive")
        normalized_version = f"v{version}"
    else:
        normalized_version = version.strip()
        if not normalized_version:
            raise ConfigurationError("cache namespace version must not be empty")
        if ":" in normalized_version:
            raise ConfigurationError("cache namespace version must not contain ':'")
    return f"{normalized_name}:{normalized_version}"


def cache_directory(app_name: str, *, base_path: str | Path | None = None) -> Path:
    """Return a conventional per-application cache directory path.

    The helper does not create the directory. It only centralizes the boring
    platform/env-var selection used by docs and examples.
    """

    normalized_name = app_name.strip()
    if not normalized_name:
        raise ConfigurationError("cache directory app name must not be empty")
    if Path(normalized_name).name != normalized_name:
        raise ConfigurationError("cache directory app name must be a single path segment")

    if base_path is not None:
        return Path(base_path).expanduser() / normalized_name

    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA")
        base = Path(root).expanduser() if root else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        root = os.environ.get("XDG_CACHE_HOME")
        base = Path(root).expanduser() if root else Path.home() / ".cache"
    return base / normalized_name


def _default_cache_key(
    args: tuple[object, ...],
    kwargs: dict[str, object],
    *,
    typed: bool,
    namespace: str | None = None,
) -> Hashable:
    key_parts: tuple[object, ...] = ()
    if namespace is not None:
        key_parts += (namespace,)
    key_parts += args
    if kwargs:
        key_parts += (_KW_MARKER,)
        key_parts += tuple(sorted(kwargs.items()))
    if typed:
        key_parts += (_TYPE_MARKER,)
        key_parts += tuple(type(arg) for arg in args)
        if kwargs:
            key_parts += tuple((name, type(value)) for name, value in sorted(kwargs.items()))
    return _ensure_hashable(key_parts)


def cache_result(
    *,
    ttl: float | None = None,
    maxsize: int | None = 128,
    key: Callable[..., Hashable] | None = None,
    typed: bool = False,
    cache_exceptions: bool = False,
    refresh_ttl_on_hit: bool = False,
    coalesce_misses: bool = False,
    clock: Clock | None = None,
    backend: CacheBackend | None = None,
    namespace: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Cache results from a synchronous function using a configurable backend.

    Async callables are intentionally rejected for ``v0.1.0`` until async cache
    semantics are designed separately.
    """

    if namespace is not None and not namespace.strip():
        raise ConfigurationError("namespace must not be empty")

    cache_backend = backend or MemoryCacheBackend(
        ttl=ttl,
        maxsize=maxsize,
        refresh_ttl_on_hit=refresh_ttl_on_hit,
        clock=clock,
    )
    if backend is not None:
        cache_backend.info()

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if is_async_callable(func):
            raise ConfigurationError("cache_result does not support async functions yet")

        def make_key(args: tuple[object, ...], kwargs: dict[str, object]) -> Hashable:
            if key is not None:
                return _ensure_hashable(key(*args, **kwargs))
            return _default_cache_key(args, kwargs, typed=typed, namespace=namespace)

        def cache_info() -> CacheInfo:
            return cache_backend.info()

        def cache_clear() -> None:
            cache_backend.clear()

        in_flight_lock = RLock()
        in_flight: dict[Hashable, Event] = {}
        total_waiters = 0
        total_wait_seconds = 0.0

        def cache_coalescing_info() -> CacheCoalescingInfo:
            with in_flight_lock:
                return CacheCoalescingInfo(
                    current_in_flight=len(in_flight),
                    total_waiters=total_waiters,
                    total_wait_seconds=total_wait_seconds,
                )

        def cached_entry_value(entry: _CacheEntry) -> R:
            if entry.is_exception:
                raise cast(BaseException, entry.payload)
            return cast(R, entry.payload)

        def compute_and_store(
            cache_key: Hashable, args: tuple[object, ...], kwargs: dict[str, object]
        ) -> R:
            try:
                result = func(*cast(Any, args), **cast(Any, kwargs))
            except Exception as exc:
                if cache_exceptions:
                    cache_backend.set_exception(cache_key, exc)
                raise

            cache_backend.set_value(cache_key, result)
            return result

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal total_wait_seconds, total_waiters

            cache_key = make_key(cast(tuple[object, ...], args), cast(dict[str, object], kwargs))
            entry = cache_backend.get(cache_key)
            if entry is not None:
                return cached_entry_value(entry)
            if not coalesce_misses:
                return compute_and_store(
                    cache_key, cast(tuple[object, ...], args), cast(dict[str, object], kwargs)
                )

            while True:
                with in_flight_lock:
                    in_flight_event = in_flight.get(cache_key)
                    if in_flight_event is None:
                        in_flight_event = Event()
                        in_flight[cache_key] = in_flight_event
                        producer = True
                    else:
                        producer = False

                if producer:
                    try:
                        return compute_and_store(
                            cache_key,
                            cast(tuple[object, ...], args),
                            cast(dict[str, object], kwargs),
                        )
                    finally:
                        with in_flight_lock:
                            if in_flight.get(cache_key) is in_flight_event:
                                in_flight.pop(cache_key, None)
                            in_flight_event.set()

                wait_started = monotonic()
                in_flight_event.wait()
                wait_seconds = monotonic() - wait_started
                with in_flight_lock:
                    total_waiters += 1
                    total_wait_seconds += wait_seconds
                entry = cache_backend.get(cache_key)
                if entry is not None:
                    return cached_entry_value(entry)

        wrapped = mirror_metadata(wrapper, func)
        wrapped_with_cache_api = cast(Any, wrapped)
        wrapped_with_cache_api.cache_info = cache_info
        wrapped_with_cache_api.cache_clear = cache_clear
        wrapped_with_cache_api.cache_coalescing_info = cache_coalescing_info
        return wrapped

    return decorator
