"""Optional Redis-backed cache backend."""

from __future__ import annotations

import base64
import hashlib
import json
import pickle
from collections.abc import Hashable, Iterable
from typing import Protocol, cast, runtime_checkable

from pydecorators.cache_result import (
    CacheInfo,
    CacheSerializer,
    JsonCacheSerializer,
    PickleCacheSerializer,
    _CacheEntry,
)
from pydecorators.exceptions import CacheSerializationError, ConfigurationError


@runtime_checkable
class RedisCacheClient(Protocol):
    """Small Redis client protocol used by ``RedisCacheBackend``."""

    def get(self, name: str) -> bytes | str | int | None:
        """Return a value by key."""

    def set(
        self,
        name: str,
        value: bytes | str,
        *,
        ex: int | None = None,
    ) -> object:
        """Set a value by key with an optional expiry in seconds."""

    def delete(self, *names: str) -> int:
        """Delete one or more keys."""

    def incr(self, name: str) -> int:
        """Increment and return an integer counter."""

    def scan_iter(self, match: str) -> Iterable[str | bytes]:
        """Yield keys matching a Redis glob pattern."""


class RedisCacheBackend:
    """Redis-backed cache backend for optional distributed/local service caches."""

    def __init__(
        self,
        *,
        client: RedisCacheClient | None = None,
        url: str | None = None,
        key_prefix: str,
        ttl: int | None = None,
        maxsize: int | None = None,
        serializer: CacheSerializer | None = None,
    ) -> None:
        if not key_prefix.strip():
            raise ConfigurationError("RedisCacheBackend key_prefix must not be empty")
        if any(character.isspace() for character in key_prefix):
            raise ConfigurationError("RedisCacheBackend key_prefix must not contain whitespace")
        if ttl is not None and ttl <= 0:
            raise ConfigurationError("ttl must be greater than zero when provided")
        if maxsize is not None and maxsize <= 0:
            raise ConfigurationError("maxsize must be greater than zero when provided")
        if client is not None and url is not None:
            raise ConfigurationError("provide either Redis client or url, not both")

        self._client = client if client is not None else _client_from_url(url)
        self._key_prefix = key_prefix.strip().rstrip(":")
        self._ttl = ttl
        self._maxsize = maxsize
        self._serializer = serializer or PickleCacheSerializer()

    def get(self, key: Hashable) -> _CacheEntry | None:
        """Return a cached entry for *key*, or ``None`` after recording a miss."""

        raw = self._client.get(self._entry_key(key))
        if raw is None:
            self._increment("misses")
            return None
        try:
            entry = self._decode_entry(_to_bytes(raw))
        except CacheSerializationError:
            self._client.delete(self._entry_key(key))
            self._increment("misses")
            return None
        self._increment("hits")
        self._touch_entry(key, entry)
        return entry

    def set_value(self, key: Hashable, value: object) -> None:
        """Store a successful cached value."""

        self._set_entry(key, value, is_exception=False)

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        """Store an exception payload for later re-raising."""

        self._set_entry(key, exception, is_exception=True)

    def clear(self) -> None:
        """Clear cached entries and reset Redis-backed statistics."""

        keys = [
            *self._scan_keys(f"{self._key_prefix}:entry:*"),
            self._stats_key("hits"),
            self._stats_key("misses"),
            self._stats_key("counter"),
        ]
        if keys:
            self._client.delete(*keys)

    def info(self) -> CacheInfo:
        """Return Redis-backed cache statistics."""

        return CacheInfo(
            hits=_to_int(self._client.get(self._stats_key("hits"))),
            misses=_to_int(self._client.get(self._stats_key("misses"))),
            maxsize=self._maxsize,
            currsize=sum(1 for _ in self._scan_keys(f"{self._key_prefix}:entry:*")),
        )

    def _set_entry(self, key: Hashable, value: object, *, is_exception: bool) -> None:
        self._client.set(
            self._entry_key(key),
            self._encode_entry(value, is_exception=is_exception),
            ex=self._ttl,
        )
        self._evict_if_needed()

    def _touch_entry(self, key: Hashable, entry: _CacheEntry) -> None:
        self._client.set(
            self._entry_key(key),
            self._encode_entry(entry.payload, is_exception=entry.is_exception),
            ex=self._ttl,
        )

    def _entry_key(self, key: Hashable) -> str:
        try:
            key_bytes = pickle.dumps(key, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as exc:
            raise CacheSerializationError("failed to serialize Redis cache key") from exc
        digest = hashlib.sha256(key_bytes).hexdigest()
        return f"{self._key_prefix}:entry:{digest}"

    def _stats_key(self, name: str) -> str:
        return f"{self._key_prefix}:stats:{name}"

    def _increment(self, name: str) -> None:
        self._client.incr(self._stats_key(name))

    def _scan_keys(self, match: str) -> list[str]:
        return [_to_text(key) for key in self._client.scan_iter(match=match)]

    def _access_counter(self) -> int:
        return self._client.incr(self._stats_key("counter"))

    def _evict_if_needed(self) -> None:
        if self._maxsize is None:
            return
        entry_keys = self._scan_keys(f"{self._key_prefix}:entry:*")
        surplus = len(entry_keys) - self._maxsize
        if surplus <= 0:
            return
        ordered: list[tuple[int, str]] = []
        for entry_key in entry_keys:
            raw = self._client.get(entry_key)
            if raw is None:
                continue
            try:
                envelope = json.loads(_to_bytes(raw).decode("utf-8"))
                ordered.append((int(envelope.get("last_accessed", 0)), entry_key))
            except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                ordered.append((0, entry_key))
        ordered.sort()
        self._client.delete(*(entry_key for _, entry_key in ordered[:surplus]))

    def _encode_entry(self, value: object, *, is_exception: bool) -> bytes:
        payload = self._serializer.dumps(value)
        envelope = {
            "schema": "pydecorators.redis_cache.v1",
            "serializer_content_type": self._serializer.content_type,
            "is_exception": is_exception,
            "last_accessed": self._access_counter(),
            "payload": base64.b64encode(payload).decode("ascii"),
        }
        return json.dumps(envelope, separators=(",", ":")).encode("utf-8")

    def _decode_entry(self, data: bytes) -> _CacheEntry:
        try:
            envelope = json.loads(data.decode("utf-8"))
            if envelope["schema"] != "pydecorators.redis_cache.v1":
                raise CacheSerializationError("unsupported Redis cache entry schema")
            if envelope["serializer_content_type"] != self._serializer.content_type:
                raise CacheSerializationError("Redis cache serializer content type mismatch")
            payload = base64.b64decode(str(envelope["payload"]).encode("ascii"))
            value = self._serializer.loads(payload)
            return _CacheEntry(
                value,
                expires_at=None,
                is_exception=bool(envelope["is_exception"]),
            )
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CacheSerializationError("failed to deserialize Redis cache entry") from exc


# Re-exported here so Redis docs can recommend JSON payloads without importing
# the core cache module separately.
RedisJsonCacheSerializer = JsonCacheSerializer


def _client_from_url(url: str | None) -> RedisCacheClient:
    if url is None:
        raise ConfigurationError("RedisCacheBackend requires a Redis client or url")
    try:
        from redis import Redis  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ConfigurationError(
            "RedisCacheBackend requires the optional Redis dependency; install pydecorators[redis]"
        ) from exc
    return cast(RedisCacheClient, Redis.from_url(url))


def _to_bytes(value: bytes | str | int) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return str(value).encode("ascii")


def _to_text(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _to_int(value: bytes | str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, bytes):
        return int(value.decode("ascii"))
    return int(value)
