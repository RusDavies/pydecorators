"""Rate limiting decorator."""

from __future__ import annotations

import hashlib
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


class _RateLimiter(Protocol):
    def reserve_or_delay(self, key: Hashable) -> float | None:
        """Reserve a call slot or return seconds to wait before retrying."""


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
    )
    clock_func = clock or monotonic

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        limiter_namespace = namespace or f"{func.__module__}.{func.__qualname__}"
        limiter: _RateLimiter
        if interprocess:
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


def _validate_rate_limit_config(
    *,
    calls: int,
    period: float,
    key: RateLimitKey | None,
    mode: RateLimitMode,
    interprocess: bool,
    storage_path: str | os.PathLike[str] | None,
    namespace: str | None,
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
    if interprocess and storage_path is None:
        raise ConfigurationError("storage_path is required when interprocess is True")
    if namespace is not None and not namespace.strip():
        raise ConfigurationError("namespace must not be empty when provided")


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
            "rate limit bucket key must be pickle-serializable when interprocess is True"
        ) from exc
    return hashlib.sha256(key_bytes).hexdigest()
