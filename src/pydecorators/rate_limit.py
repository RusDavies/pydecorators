"""Rate limiting decorator."""

from __future__ import annotations

import hashlib
import math
import os
import pickle
import sqlite3
from collections import defaultdict, deque
from collections.abc import Callable, Hashable
from pathlib import Path
from threading import RLock
from typing import Any, Literal, Protocol, cast

from pydecorators._core import (
    async_sleep,
    is_async_callable,
    mirror_metadata,
    monotonic,
    sync_sleep,
)
from pydecorators._typing import P, R
from pydecorators.exceptions import ConfigurationError, RateLimitExceeded

RateLimitMode = Literal["raise", "block"]
RateLimitKey = Callable[..., Hashable]

_REDIS_GLOB_METACHARACTERS = frozenset("*?[]")
_REDIS_RATE_LIMIT_SCRIPT = """
local events_key = KEYS[1]
local sequence_key = KEYS[2]
local now = tonumber(ARGV[1])
local period = tonumber(ARGV[2])
local calls = tonumber(ARGV[3])
local ttl_ms = math.max(1, math.ceil(period * 1000))

redis.call("ZREMRANGEBYSCORE", events_key, "-inf", now - period)
local count = redis.call("ZCARD", events_key)
if count < calls then
    local sequence = redis.call("INCR", sequence_key)
    redis.call("ZADD", events_key, now, tostring(now) .. ":" .. tostring(sequence))
    redis.call("PEXPIRE", events_key, ttl_ms)
    redis.call("PEXPIRE", sequence_key, ttl_ms)
    return {0, 0}
end

local oldest = redis.call("ZRANGE", events_key, 0, 0, "WITHSCORES")[2]
local wait_ms = math.max(0, math.ceil((tonumber(oldest) + period - now) * 1000))
return {1, wait_ms}
"""


class _RateLimiter(Protocol):
    def reserve_or_delay(self, key: Hashable) -> float | None:
        """Reserve a call slot or return seconds to wait before retrying."""


class _RedisRateLimitClient(Protocol):
    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object:
        """Evaluate a Redis Lua script."""


def rate_limit(
    *,
    calls: int,
    period: float,
    key: RateLimitKey | None = None,
    mode: RateLimitMode = "raise",
    clock: Callable[[], float] | None = None,
    sleep: Callable[[float], object] | None = None,
    interprocess: bool = False,
    storage_path: str | os.PathLike[str] | None = None,
    namespace: str | None = None,
    distributed: bool = False,
    redis_client: object | None = None,
    redis_url: str | None = None,
    redis_key_prefix: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Limit calls to a sync or async callable over a sliding time window."""

    _validate_rate_limit_config(
        calls=calls,
        period=period,
        key=key,
        mode=mode,
        interprocess=interprocess,
        storage_path=storage_path,
        namespace=namespace,
        distributed=distributed,
        redis_client=redis_client,
        redis_url=redis_url,
        redis_key_prefix=redis_key_prefix,
    )
    clock_func = clock or monotonic

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        limiter_namespace = namespace or f"{func.__module__}.{func.__qualname__}"
        limiter: _RateLimiter
        if distributed:
            limiter = _RedisSlidingWindowLimiter(
                calls=calls,
                period=period,
                clock=clock_func,
                client=_redis_client(redis_client=redis_client, redis_url=redis_url),
                key_prefix=cast(str, redis_key_prefix),
                namespace=limiter_namespace,
            )
        elif interprocess:
            limiter = _SQLiteSlidingWindowLimiter(
                calls=calls,
                period=period,
                clock=clock_func,
                storage_path=cast(str | os.PathLike[str], storage_path),
                namespace=limiter_namespace,
            )
        else:
            limiter = _SlidingWindowLimiter(calls=calls, period=period, clock=clock_func)

        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)
            async_sleep_func = cast(Callable[[float], Any], sleep or async_sleep)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                bucket_key = _bucket_key(key, args, kwargs)
                while True:
                    wait_seconds = limiter.reserve_or_delay(bucket_key)
                    if wait_seconds is None:
                        result = async_func(*args, **kwargs)
                        if hasattr(result, "__await__"):
                            result = await result
                        return result
                    if mode == "raise":
                        raise RateLimitExceeded(retry_after=wait_seconds)
                    await async_sleep_func(wait_seconds)

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        sync_sleep_func = sleep or sync_sleep

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bucket_key = _bucket_key(key, args, kwargs)
            while True:
                wait_seconds = limiter.reserve_or_delay(bucket_key)
                if wait_seconds is None:
                    return func(*args, **kwargs)
                if mode == "raise":
                    raise RateLimitExceeded(retry_after=wait_seconds)
                sync_sleep_func(wait_seconds)

        return mirror_metadata(wrapper, func)

    return decorate


class _SlidingWindowLimiter:
    def __init__(self, *, calls: int, period: float, clock: Callable[[], float]) -> None:
        self._calls = calls
        self._period = period
        self._clock = clock
        self._lock = RLock()
        self._windows: defaultdict[Hashable, deque[float]] = defaultdict(deque)

    def reserve_or_delay(self, key: Hashable) -> float | None:
        """Reserve a call slot or return seconds to wait before retrying."""

        now = self._clock()
        with self._lock:
            self._prune_idle_windows(now)
            window = self._windows[key]
            if len(window) < self._calls:
                window.append(now)
                return None
            oldest = window[0]
            return max(0.0, oldest + self._period - now)

    def _prune(self, window: deque[float], now: float) -> None:
        cutoff = now - self._period
        while window and window[0] <= cutoff:
            window.popleft()

    def _prune_idle_windows(self, now: float) -> None:
        empty_keys = []
        for key, window in self._windows.items():
            self._prune(window, now)
            if not window:
                empty_keys.append(key)
        for key in empty_keys:
            self._windows.pop(key, None)


class _SQLiteSlidingWindowLimiter:
    def __init__(
        self,
        *,
        calls: int,
        period: float,
        clock: Callable[[], float],
        storage_path: str | os.PathLike[str],
        namespace: str,
    ) -> None:
        self._calls = calls
        self._period = period
        self._clock = clock
        self._storage_path = Path(storage_path)
        self._namespace = namespace
        self._initialize_database()

    def reserve_or_delay(self, key: Hashable) -> float | None:
        """Reserve a cross-process call slot or return seconds to wait."""

        now = self._clock()
        bucket_key = _stored_bucket_key(key)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                DELETE FROM rate_limit_events
                WHERE namespace = ? AND bucket_key = ? AND timestamp <= ?
                """,
                (self._namespace, bucket_key, now - self._period),
            )
            row = connection.execute(
                """
                SELECT COUNT(*), MIN(timestamp)
                FROM rate_limit_events
                WHERE namespace = ? AND bucket_key = ?
                """,
                (self._namespace, bucket_key),
            ).fetchone()
            count = int(row[0])
            oldest = cast(float | None, row[1])
            if count < self._calls:
                connection.execute(
                    """
                    INSERT INTO rate_limit_events(namespace, bucket_key, timestamp)
                    VALUES (?, ?, ?)
                    """,
                    (self._namespace, bucket_key, now),
                )
                connection.commit()
                return None
            connection.commit()
            return max(0.0, cast(float, oldest) + self._period - now)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize_database(self) -> None:
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limit_events (
                    namespace TEXT NOT NULL,
                    bucket_key TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS rate_limit_events_window
                ON rate_limit_events(namespace, bucket_key, timestamp)
                """
            )
            connection.commit()
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._storage_path, timeout=30.0, isolation_level=None)
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection


class _RedisSlidingWindowLimiter:
    def __init__(
        self,
        *,
        calls: int,
        period: float,
        clock: Callable[[], float],
        client: _RedisRateLimitClient,
        key_prefix: str,
        namespace: str,
    ) -> None:
        self._calls = calls
        self._period = period
        self._clock = clock
        self._client = client
        self._key_prefix = key_prefix.strip().rstrip(":")
        self._namespace = namespace

    def reserve_or_delay(self, key: Hashable) -> float | None:
        """Reserve a Redis-backed distributed call slot or return seconds to wait."""

        now = self._clock()
        events_key, sequence_key = self._redis_keys(key)
        result = self._client.eval(
            _REDIS_RATE_LIMIT_SCRIPT,
            2,
            events_key,
            sequence_key,
            repr(now),
            repr(self._period),
            str(self._calls),
        )
        status, wait_ms = _redis_script_result(result)
        if status == 0:
            return None
        return max(0.0, wait_ms / 1000)

    def _redis_keys(self, key: Hashable) -> tuple[str, str]:
        namespace_digest = _digest_text(self._namespace)
        bucket_digest = _stored_bucket_key(key)
        # The hash tag keeps the event and sequence keys in one Redis Cluster slot.
        base_key = f"{self._key_prefix}:rate_limit:{{{namespace_digest}:{bucket_digest}}}"
        return base_key, f"{base_key}:sequence"


def _validate_rate_limit_config(
    *,
    calls: int,
    period: float,
    key: RateLimitKey | None,
    mode: RateLimitMode,
    interprocess: bool,
    storage_path: str | os.PathLike[str] | None,
    namespace: str | None,
    distributed: bool,
    redis_client: object | None,
    redis_url: str | None,
    redis_key_prefix: str | None,
) -> None:
    if calls <= 0:
        raise ConfigurationError("calls must be greater than zero")
    if period <= 0:
        raise ConfigurationError("period must be greater than zero")
    if key is not None and not callable(key):
        raise ConfigurationError("key must be callable when provided")
    if mode not in {"raise", "block"}:
        raise ConfigurationError('mode must be "raise" or "block"')
    if not isinstance(interprocess, bool):
        raise ConfigurationError("interprocess must be a boolean")
    if not isinstance(distributed, bool):
        raise ConfigurationError("distributed must be a boolean")
    if interprocess and distributed:
        raise ConfigurationError("interprocess and distributed modes are mutually exclusive")
    if interprocess and storage_path is None:
        raise ConfigurationError("storage_path is required when interprocess is True")
    if not interprocess and storage_path is not None:
        raise ConfigurationError("storage_path is only supported when interprocess is True")
    if namespace is not None and not namespace.strip():
        raise ConfigurationError("namespace must not be empty when provided")
    if not distributed:
        if redis_client is not None or redis_url is not None or redis_key_prefix is not None:
            raise ConfigurationError("Redis options require distributed=True")
        return
    if redis_client is None and redis_url is None:
        raise ConfigurationError("redis_client or redis_url is required when distributed is True")
    if redis_client is not None and redis_url is not None:
        raise ConfigurationError("provide either Redis client or redis_url, not both")
    if redis_client is not None and not callable(getattr(redis_client, "eval", None)):
        raise ConfigurationError("redis_client must provide an eval method")
    _validate_redis_key_prefix(redis_key_prefix)


def _bucket_key(
    key: RateLimitKey | None,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> Hashable:
    if key is None:
        return "__global__"
    try:
        return key(*args, **kwargs)
    except TypeError:
        raise


def _stored_bucket_key(key: Hashable) -> str:
    try:
        key_bytes = pickle.dumps(key, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as exc:
        raise TypeError(
            "rate limit bucket key must be pickle-serializable when interprocess or distributed "
            "mode is enabled"
        ) from exc
    return hashlib.sha256(key_bytes).hexdigest()


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_redis_key_prefix(redis_key_prefix: str | None) -> None:
    if redis_key_prefix is None or not redis_key_prefix.strip():
        raise ConfigurationError("redis_key_prefix is required when distributed is True")
    if any(character.isspace() for character in redis_key_prefix):
        raise ConfigurationError("redis_key_prefix must not contain whitespace")
    if any(character in _REDIS_GLOB_METACHARACTERS for character in redis_key_prefix):
        raise ConfigurationError("redis_key_prefix must not contain Redis glob metacharacters")


def _redis_client(*, redis_client: object | None, redis_url: str | None) -> _RedisRateLimitClient:
    if redis_client is not None:
        return cast(_RedisRateLimitClient, redis_client)
    try:
        import redis
    except ImportError as exc:
        raise ConfigurationError(
            "Redis rate limiting from url requires installing blakemere-wraptools[redis]"
        ) from exc
    return cast(_RedisRateLimitClient, redis.Redis.from_url(cast(str, redis_url)))


def _redis_script_result(result: object) -> tuple[int, int]:
    if not isinstance(result, list | tuple) or len(result) != 2:
        raise RuntimeError("Redis rate limit script returned an invalid result")
    status = int(result[0])
    wait_ms = math.ceil(float(result[1]))
    if status not in {0, 1}:
        raise RuntimeError("Redis rate limit script returned an invalid status")
    return status, wait_ms
