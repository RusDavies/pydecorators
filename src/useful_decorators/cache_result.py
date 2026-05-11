"""In-memory result caching decorator."""

from __future__ import annotations

import pickle
import sqlite3
from collections import OrderedDict
from collections.abc import Callable, Hashable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Protocol, cast, runtime_checkable

from useful_decorators._core import is_async_callable, mirror_metadata, monotonic
from useful_decorators._typing import Clock, P, R
from useful_decorators.exceptions import (
    CacheBackendClosedError,
    CacheKeyError,
    CacheSerializationError,
    ConfigurationError,
)

_KW_MARKER = object()
_TYPE_MARKER = object()


@dataclass(frozen=True, slots=True)
class CacheInfo:
    """Cache statistics exposed by ``cache_info()`` on cached functions."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int


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
        clock: Clock | None = None,
    ) -> None:
        if ttl is not None and ttl <= 0:
            raise ConfigurationError("ttl must be greater than zero when provided")
        if maxsize is not None and maxsize <= 0:
            raise ConfigurationError("maxsize must be greater than zero when provided")

        self._ttl = ttl
        self._maxsize = maxsize
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
    """SQLite-backed local persistent cache backend.

    This first slice initializes the database schema. Cache operations are
    implemented in later slices.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        serializer: CacheSerializer | None = None,
        clock: Clock | None = None,
    ) -> None:
        if ttl is not None and ttl <= 0:
            raise ConfigurationError("ttl must be greater than zero when provided")
        if maxsize is not None and maxsize <= 0:
            raise ConfigurationError("maxsize must be greater than zero when provided")

        self.path = Path(path)
        self._ttl = ttl
        self._maxsize = maxsize
        self._key_serializer = PickleCacheSerializer()
        self._serializer = serializer or PickleCacheSerializer()
        self._clock = clock or monotonic
        self._lock = RLock()
        self._closed = False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._initialize_schema()

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
                    self._record_miss()
                    return None

                self._connection.execute(
                    "UPDATE cache_entries SET last_accessed = ? WHERE key = ?",
                    (now, serialized_key),
                )
                self._record_hit()
                return _CacheEntry(
                    self._deserialize_payload(payload),
                    expires_at=expires_at,
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

    def _record_miss(self) -> None:
        self._connection.execute("UPDATE cache_stats SET misses = misses + 1 WHERE id = 1")

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


def _ensure_hashable(value: object) -> Hashable:
    try:
        hash(value)
    except TypeError as exc:
        raise CacheKeyError("cache key must be hashable") from exc
    return value


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

    cache_backend = backend or MemoryCacheBackend(ttl=ttl, maxsize=maxsize, clock=clock)

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

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache_key = make_key(cast(tuple[object, ...], args), cast(dict[str, object], kwargs))
            entry = cache_backend.get(cache_key)
            if entry is not None:
                if entry.is_exception:
                    raise cast(BaseException, entry.payload)
                return cast(R, entry.payload)

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                if cache_exceptions:
                    cache_backend.set_exception(cache_key, exc)
                raise

            cache_backend.set_value(cache_key, result)
            return result

        wrapped = mirror_metadata(wrapper, func)
        wrapped_with_cache_api = cast(Any, wrapped)
        wrapped_with_cache_api.cache_info = cache_info
        wrapped_with_cache_api.cache_clear = cache_clear
        return wrapped

    return decorator
