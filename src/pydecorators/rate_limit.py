"""Rate limiting decorator."""

from __future__ import annotations

import hashlib
import math
import os
import pickle
import sqlite3
import time
from collections import defaultdict, deque
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Any, Literal, Protocol, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
RateLimitCost = int | Callable[[tuple[object, ...], dict[str, object]], int]
CalendarRateLimitUnit = Literal["minute", "hour", "day", "week"]
CalendarWeekStart = Literal["monday", "sunday"]

_REDIS_GLOB_METACHARACTERS = frozenset("*?[]")
_REDIS_RATE_LIMIT_SCRIPT = """
local sequence_key = KEYS[1]
local now = tonumber(ARGV[1])
local cost = tonumber(ARGV[2])
local window_count = tonumber(ARGV[3])
local max_wait_ms = 0

for index = 1, window_count do
    local events_key = KEYS[index + 1]
    local prune_before = tonumber(ARGV[(index * 5) - 1])
    local calls = tonumber(ARGV[index * 5])
    local period = tonumber(ARGV[(index * 5) + 1])
    local reset_at = tonumber(ARGV[(index * 5) + 2])

    redis.call("ZREMRANGEBYSCORE", events_key, "-inf", prune_before)
    local events = redis.call("ZRANGE", events_key, 0, -1, "WITHSCORES")
    local used = 0
    for event_index = 1, #events, 2 do
        local member = tostring(events[event_index])
        local event_cost = 1
        if string.match(member, "^[^:]+:[^:]+:[^:]+:") then
            event_cost = tonumber(string.match(member, "^([^:]+):")) or 1
        end
        used = used + event_cost
    end
    if used + cost > calls then
        local wait_seconds = 0
        if reset_at > 0 then
            wait_seconds = reset_at - now
        else
            local freed = 0
            for event_index = 1, #events, 2 do
                local member = tostring(events[event_index])
                local score = tonumber(events[event_index + 1])
                local event_cost = 1
                if string.match(member, "^[^:]+:[^:]+:[^:]+:") then
                    event_cost = tonumber(string.match(member, "^([^:]+):")) or 1
                end
                freed = freed + event_cost
                if used - freed + cost <= calls then
                    wait_seconds = score + period - now
                    break
                end
            end
            if wait_seconds == 0 then
                wait_seconds = period
            end
        end
        local wait_ms = math.max(0, math.ceil(wait_seconds * 1000))
        if wait_ms > max_wait_ms then
            max_wait_ms = wait_ms
        end
    end
end

if max_wait_ms > 0 then
    return {1, max_wait_ms}
end

local sequence = redis.call("INCR", sequence_key)
local max_ttl_ms = 1
for index = 1, window_count do
    local events_key = KEYS[index + 1]
    local ttl = tonumber(ARGV[(index * 5) + 3])
    local ttl_ms = math.max(1, math.ceil(ttl * 1000))
    local member = tostring(cost) .. ":" .. tostring(now) .. ":" .. tostring(index)
    member = member .. ":" .. tostring(sequence)
    redis.call("ZADD", events_key, now, member)
    redis.call("PEXPIRE", events_key, ttl_ms)
    if ttl_ms > max_ttl_ms then
        max_ttl_ms = ttl_ms
    end
end
redis.call("PEXPIRE", sequence_key, max_ttl_ms)
return {0, 0}
"""


@dataclass(frozen=True)
class RateLimitWindow:
    """A sliding rate-limit window.

    ``calls`` is the number of calls admitted within ``period`` seconds.
    """

    calls: int
    period: float
    name: str | None = None


@dataclass(frozen=True)
class CalendarRateLimitWindow:
    """A wall-clock aligned rate-limit window.

    ``unit`` selects the aligned calendar bucket in ``timezone``. Calendar weeks start on
    Monday by default.
    """

    calls: int
    unit: CalendarRateLimitUnit
    name: str | None = None
    timezone: str = "UTC"
    week_start: CalendarWeekStart = "monday"


@dataclass(frozen=True)
class _NormalizedRateLimitWindow:
    calls: int
    period: float
    window_id: str
    kind: Literal["sliding", "calendar"] = "sliding"
    unit: CalendarRateLimitUnit | None = None
    timezone: ZoneInfo | None = None
    week_start: CalendarWeekStart = "monday"


@dataclass(frozen=True)
class _RuntimeRateLimitWindow:
    calls: int
    period: float
    window_id: str
    prune_before: float
    reset_at: float | None
    ttl: float


@dataclass(frozen=True)
class _RateLimitEvent:
    timestamp: float
    cost: int


class _RateLimiter(Protocol):
    def reserve_or_delay(self, key: Hashable, cost: int) -> float | None:
        """Reserve a call slot or return seconds to wait before retrying."""


class _RedisRateLimitClient(Protocol):
    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object:
        """Evaluate a Redis Lua script."""


def rate_limit(
    *,
    calls: int | None = None,
    period: float | None = None,
    windows: Sequence[RateLimitWindow | CalendarRateLimitWindow | tuple[int, float]] | None = None,
    key: RateLimitKey | None = None,
    mode: RateLimitMode = "raise",
    clock: Callable[[], float] | None = None,
    sleep: Callable[[float], object] | None = None,
    cost: RateLimitCost = 1,
    interprocess: bool = False,
    storage_path: str | os.PathLike[str] | None = None,
    namespace: str | None = None,
    distributed: bool = False,
    redis_client: object | None = None,
    redis_url: str | None = None,
    redis_key_prefix: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Limit calls to a sync or async callable over a sliding time window."""

    normalized_windows = _normalize_rate_limit_windows(calls=calls, period=period, windows=windows)
    _validate_rate_limit_config(
        windows=normalized_windows,
        key=key,
        mode=mode,
        cost=cost,
        interprocess=interprocess,
        storage_path=storage_path,
        namespace=namespace,
        distributed=distributed,
        redis_client=redis_client,
        redis_url=redis_url,
        redis_key_prefix=redis_key_prefix,
    )
    clock_func = clock or (time.time if _has_calendar_windows(normalized_windows) else monotonic)

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        limiter_namespace = namespace or f"{func.__module__}.{func.__qualname__}"
        limiter: _RateLimiter
        if distributed:
            limiter = _RedisSlidingWindowLimiter(
                windows=normalized_windows,
                clock=clock_func,
                client=_redis_client(redis_client=redis_client, redis_url=redis_url),
                key_prefix=cast(str, redis_key_prefix),
                namespace=limiter_namespace,
            )
        elif interprocess:
            limiter = _SQLiteSlidingWindowLimiter(
                windows=normalized_windows,
                clock=clock_func,
                storage_path=cast(str | os.PathLike[str], storage_path),
                namespace=limiter_namespace,
            )
        else:
            limiter = _SlidingWindowLimiter(windows=normalized_windows, clock=clock_func)

        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)
            async_sleep_func = cast(Callable[[float], Any], sleep or async_sleep)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                call_cost = _resolve_rate_limit_cost(cost, args, kwargs)
                if _cost_exceeds_capacity(call_cost, normalized_windows):
                    raise RateLimitExceeded(retry_after=math.inf)
                bucket_key = _bucket_key(key, args, kwargs)
                while True:
                    wait_seconds = limiter.reserve_or_delay(bucket_key, call_cost)
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
            call_cost = _resolve_rate_limit_cost(cost, args, kwargs)
            if _cost_exceeds_capacity(call_cost, normalized_windows):
                raise RateLimitExceeded(retry_after=math.inf)
            bucket_key = _bucket_key(key, args, kwargs)
            while True:
                wait_seconds = limiter.reserve_or_delay(bucket_key, call_cost)
                if wait_seconds is None:
                    return func(*args, **kwargs)
                if mode == "raise":
                    raise RateLimitExceeded(retry_after=wait_seconds)
                sync_sleep_func(wait_seconds)

        return mirror_metadata(wrapper, func)

    return decorate


class _SlidingWindowLimiter:
    def __init__(
        self, *, windows: Sequence[_NormalizedRateLimitWindow], clock: Callable[[], float]
    ) -> None:
        self._windows_config = tuple(windows)
        self._clock = clock
        self._lock = RLock()
        self._windows: defaultdict[Hashable, dict[str, deque[_RateLimitEvent]]] = defaultdict(dict)

    def reserve_or_delay(self, key: Hashable, cost: int) -> float | None:
        """Reserve a call slot or return seconds to wait before retrying."""

        now = self._clock()
        with self._lock:
            self._prune_idle_windows(now)
            runtime_windows = _runtime_windows(self._windows_config, now)
            bucket_windows = self._windows[key]
            wait_seconds = 0.0
            for window_config in runtime_windows:
                window = bucket_windows.setdefault(window_config.window_id, deque())
                self._prune(window, window_config.prune_before)
                wait_seconds = max(
                    wait_seconds,
                    _window_wait_seconds(window, window_config, now=now, cost=cost),
                )
            if wait_seconds > 0:
                return max(0.0, wait_seconds)
            for window_config in runtime_windows:
                bucket_windows.setdefault(window_config.window_id, deque()).append(
                    _RateLimitEvent(timestamp=now, cost=cost)
                )
            return None

    def _prune(self, window: deque[_RateLimitEvent], prune_before: float) -> None:
        while window and window[0].timestamp <= prune_before:
            window.popleft()

    def _prune_idle_windows(self, now: float) -> None:
        empty_keys = []
        cleanup_before = now - _max_window_cleanup_period(self._windows_config)
        for key, bucket_windows in self._windows.items():
            empty_window_ids = []
            for window_id, window in bucket_windows.items():
                self._prune(window, cleanup_before)
                if not window:
                    empty_window_ids.append(window_id)
            for window_id in empty_window_ids:
                bucket_windows.pop(window_id, None)
            if not bucket_windows:
                empty_keys.append(key)
        for key in empty_keys:
            self._windows.pop(key, None)


def _window_wait_seconds(
    events: Sequence[_RateLimitEvent],
    window: _RuntimeRateLimitWindow,
    *,
    now: float,
    cost: int,
) -> float:
    used = sum(event.cost for event in events)
    if used + cost <= window.calls:
        return 0.0
    if window.reset_at is not None:
        return max(0.0, window.reset_at - now)
    freed = 0
    for event in events:
        freed += event.cost
        if used - freed + cost <= window.calls:
            return max(0.0, event.timestamp + window.period - now)
    return max(0.0, window.period)


class _SQLiteSlidingWindowLimiter:
    def __init__(
        self,
        *,
        windows: Sequence[_NormalizedRateLimitWindow],
        clock: Callable[[], float],
        storage_path: str | os.PathLike[str],
        namespace: str,
    ) -> None:
        self._windows = tuple(windows)
        self._clock = clock
        self._storage_path = Path(storage_path)
        self._namespace = namespace
        self._initialize_database()

    def reserve_or_delay(self, key: Hashable, cost: int) -> float | None:
        """Reserve a cross-process call slot or return seconds to wait."""

        now = self._clock()
        runtime_windows = _runtime_windows(self._windows, now)
        bucket_key = _stored_bucket_key(key)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                DELETE FROM rate_limit_events
                WHERE namespace = ? AND bucket_key = ? AND timestamp <= ?
                """,
                (self._namespace, bucket_key, now - _max_window_cleanup_period(self._windows)),
            )
            wait_seconds = 0.0
            for window in runtime_windows:
                connection.execute(
                    """
                    DELETE FROM rate_limit_events
                    WHERE namespace = ? AND bucket_key = ? AND window_id = ? AND timestamp <= ?
                    """,
                    (self._namespace, bucket_key, window.window_id, window.prune_before),
                )
                rows = connection.execute(
                    """
                    SELECT timestamp, cost
                    FROM rate_limit_events
                    WHERE namespace = ? AND bucket_key = ? AND window_id = ?
                    ORDER BY timestamp ASC
                    """,
                    (self._namespace, bucket_key, window.window_id),
                ).fetchall()
                events = [
                    _RateLimitEvent(timestamp=float(row[0]), cost=int(row[1])) for row in rows
                ]
                wait_seconds = max(
                    wait_seconds,
                    _window_wait_seconds(events, window, now=now, cost=cost),
                )
            if wait_seconds <= 0:
                rows = [
                    (self._namespace, bucket_key, window.window_id, now, cost)
                    for window in runtime_windows
                ]
                connection.execute(
                    """
                    INSERT INTO rate_limit_events(namespace, bucket_key, window_id, timestamp, cost)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    rows[0],
                )
                if len(rows) > 1:
                    connection.executemany(
                        """
                        INSERT INTO rate_limit_events(
                            namespace, bucket_key, window_id, timestamp, cost
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        rows[1:],
                    )
                connection.commit()
                return None
            connection.commit()
            return max(0.0, wait_seconds)
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
                    window_id TEXT NOT NULL DEFAULT 'default',
                    timestamp REAL NOT NULL,
                    cost INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            columns = {
                str(row[1]) for row in connection.execute("PRAGMA table_info(rate_limit_events)")
            }
            if "window_id" not in columns:
                connection.execute(
                    """
                    ALTER TABLE rate_limit_events
                    ADD COLUMN window_id TEXT NOT NULL DEFAULT 'default'
                    """
                )
            if "cost" not in columns:
                connection.execute(
                    """
                    ALTER TABLE rate_limit_events
                    ADD COLUMN cost INTEGER NOT NULL DEFAULT 1
                    """
                )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS rate_limit_events_window_v2
                ON rate_limit_events(namespace, bucket_key, window_id, timestamp)
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
        windows: Sequence[_NormalizedRateLimitWindow],
        clock: Callable[[], float],
        client: _RedisRateLimitClient,
        key_prefix: str,
        namespace: str,
    ) -> None:
        self._windows = tuple(windows)
        self._clock = clock
        self._client = client
        self._key_prefix = key_prefix.strip().rstrip(":")
        self._namespace = namespace

    def reserve_or_delay(self, key: Hashable, cost: int) -> float | None:
        """Reserve a Redis-backed distributed call slot or return seconds to wait."""

        now = self._clock()
        runtime_windows = _runtime_windows(self._windows, now)
        sequence_key, event_keys = self._redis_keys(key, runtime_windows)
        args: list[str] = [repr(now), str(cost), str(len(runtime_windows))]
        for window in runtime_windows:
            reset_at = 0.0 if window.reset_at is None else window.reset_at
            args.extend(
                [
                    repr(window.prune_before),
                    str(window.calls),
                    repr(window.period),
                    repr(reset_at),
                    repr(window.ttl),
                ]
            )
        result = self._client.eval(
            _REDIS_RATE_LIMIT_SCRIPT,
            1 + len(event_keys),
            sequence_key,
            *event_keys,
            *args,
        )
        status, wait_ms = _redis_script_result(result)
        if status == 0:
            return None
        return max(0.0, wait_ms / 1000)

    def _redis_keys(
        self, key: Hashable, windows: Sequence[_RuntimeRateLimitWindow]
    ) -> tuple[str, list[str]]:
        namespace_digest = _digest_text(self._namespace)
        bucket_digest = _stored_bucket_key(key)
        # The hash tag keeps the event and sequence keys in one Redis Cluster slot.
        base_key = f"{self._key_prefix}:rate_limit:{{{namespace_digest}:{bucket_digest}}}"
        event_keys = [f"{base_key}:window:{window.window_id}" for window in windows]
        return f"{base_key}:sequence", event_keys


def _normalize_rate_limit_windows(
    *,
    calls: int | None,
    period: float | None,
    windows: Sequence[RateLimitWindow | CalendarRateLimitWindow | tuple[int, float]] | None,
) -> tuple[_NormalizedRateLimitWindow, ...]:
    if windows is None:
        if calls is None or period is None:
            raise ConfigurationError("calls and period are required when windows is not provided")
        return (_normalize_rate_limit_window(RateLimitWindow(calls=calls, period=period), 0, True),)
    if calls is not None or period is not None:
        raise ConfigurationError("calls and period cannot be combined with windows")
    if not windows:
        raise ConfigurationError("windows must contain at least one rate limit window")
    return tuple(
        _normalize_rate_limit_window(window, index, len(windows) == 1)
        for index, window in enumerate(windows)
    )


def _normalize_rate_limit_window(
    window: RateLimitWindow | CalendarRateLimitWindow | tuple[int, float],
    index: int,
    single_window: bool,
) -> _NormalizedRateLimitWindow:
    if isinstance(window, tuple):
        if len(window) != 2:
            raise ConfigurationError("rate limit window tuples must be (calls, period)")
        public_window = RateLimitWindow(calls=window[0], period=window[1])
    elif isinstance(window, RateLimitWindow):
        public_window = window
    elif isinstance(window, CalendarRateLimitWindow):
        return _normalize_calendar_rate_limit_window(window, index, single_window)
    else:
        raise ConfigurationError(
            "windows must contain RateLimitWindow objects or (calls, period) tuples"
        )
    if public_window.calls <= 0:
        field_name = "calls" if single_window else "window calls"
        raise ConfigurationError(f"{field_name} must be greater than zero")
    if public_window.period <= 0:
        field_name = "period" if single_window else "window period"
        raise ConfigurationError(f"{field_name} must be greater than zero")
    if public_window.name is not None and not public_window.name.strip():
        raise ConfigurationError("window name must not be empty when provided")
    window_id = "default" if single_window else _window_id(public_window, index)
    return _NormalizedRateLimitWindow(
        calls=public_window.calls,
        period=float(public_window.period),
        window_id=window_id,
    )


def _normalize_calendar_rate_limit_window(
    window: CalendarRateLimitWindow, index: int, single_window: bool
) -> _NormalizedRateLimitWindow:
    if window.calls <= 0:
        field_name = "calls" if single_window else "calendar window calls"
        raise ConfigurationError(f"{field_name} must be greater than zero")
    if window.unit not in {"minute", "hour", "day", "week"}:
        raise ConfigurationError('calendar window unit must be "minute", "hour", "day", or "week"')
    if window.name is not None and not window.name.strip():
        raise ConfigurationError("calendar window name must not be empty when provided")
    if not window.timezone.strip():
        raise ConfigurationError("calendar window timezone must not be empty")
    if window.week_start not in {"monday", "sunday"}:
        raise ConfigurationError('calendar window week_start must be "monday" or "sunday"')
    try:
        timezone = ZoneInfo(window.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ConfigurationError(f"unknown calendar window timezone: {window.timezone}") from exc
    window_id = _window_id(
        RateLimitWindow(
            calls=window.calls,
            period=_calendar_unit_seconds(window.unit),
            name=window.name,
        ),
        index,
    )
    return _NormalizedRateLimitWindow(
        calls=window.calls,
        period=_calendar_unit_seconds(window.unit),
        window_id=window_id,
        kind="calendar",
        unit=window.unit,
        timezone=timezone,
        week_start=window.week_start,
    )


def _window_id(window: RateLimitWindow, index: int) -> str:
    if window.name is not None:
        return _digest_text(window.name.strip())
    return _digest_text(f"{index}:{window.calls}:{float(window.period)!r}")


def _has_calendar_windows(windows: Sequence[_NormalizedRateLimitWindow]) -> bool:
    return any(window.kind == "calendar" for window in windows)


def _runtime_windows(
    windows: Sequence[_NormalizedRateLimitWindow], now: float
) -> tuple[_RuntimeRateLimitWindow, ...]:
    runtime_windows = []
    for window in windows:
        if window.kind == "sliding":
            runtime_windows.append(
                _RuntimeRateLimitWindow(
                    calls=window.calls,
                    period=window.period,
                    window_id=window.window_id,
                    prune_before=now - window.period,
                    reset_at=None,
                    ttl=window.period,
                )
            )
            continue
        start, end = _calendar_window_bounds(window, now)
        runtime_windows.append(
            _RuntimeRateLimitWindow(
                calls=window.calls,
                period=end - start,
                window_id=f"{window.window_id}:calendar:{int(start)}",
                prune_before=start - 1e-6,
                reset_at=end,
                ttl=max(1.0, end - now),
            )
        )
    return tuple(runtime_windows)


def _calendar_window_bounds(window: _NormalizedRateLimitWindow, now: float) -> tuple[float, float]:
    if window.unit is None or window.timezone is None:
        raise RuntimeError("calendar rate limit window is missing calendar metadata")
    current = datetime.fromtimestamp(now, tz=window.timezone)
    if window.unit == "minute":
        start = current.replace(second=0, microsecond=0)
        end = start + timedelta(minutes=1)
    elif window.unit == "hour":
        start = current.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
    elif window.unit == "day":
        start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    else:
        week_start_day = 0 if window.week_start == "monday" else 6
        days_since_start = (current.weekday() - week_start_day) % 7
        start = (current - timedelta(days=days_since_start)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
    return start.timestamp(), end.timestamp()


def _calendar_unit_seconds(unit: CalendarRateLimitUnit) -> float:
    if unit == "minute":
        return 60.0
    if unit == "hour":
        return 60.0 * 60.0
    if unit == "day":
        return 24.0 * 60.0 * 60.0
    return 7.0 * 24.0 * 60.0 * 60.0


def _max_window_cleanup_period(windows: Sequence[_NormalizedRateLimitWindow]) -> float:
    return max((window.period for window in windows), default=1.0)


def _validate_rate_limit_config(
    *,
    windows: Sequence[_NormalizedRateLimitWindow],
    key: RateLimitKey | None,
    mode: RateLimitMode,
    cost: RateLimitCost,
    interprocess: bool,
    storage_path: str | os.PathLike[str] | None,
    namespace: str | None,
    distributed: bool,
    redis_client: object | None,
    redis_url: str | None,
    redis_key_prefix: str | None,
) -> None:
    if not windows:
        raise ConfigurationError("at least one rate limit window is required")
    if key is not None and not callable(key):
        raise ConfigurationError("key must be callable when provided")
    if not isinstance(cost, int) and not callable(cost):
        raise ConfigurationError("cost must be a positive integer or callable")
    if isinstance(cost, bool) or (isinstance(cost, int) and cost <= 0):
        raise ConfigurationError("cost must be greater than zero")
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


def _resolve_rate_limit_cost(
    cost: RateLimitCost,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> int:
    resolved = cost(args, kwargs) if callable(cost) else cost
    if isinstance(resolved, bool) or not isinstance(resolved, int):
        raise ConfigurationError("rate limit cost must resolve to a positive integer")
    if resolved <= 0:
        raise ConfigurationError("rate limit cost must be greater than zero")
    return resolved


def _cost_exceeds_capacity(cost: int, windows: Sequence[_NormalizedRateLimitWindow]) -> bool:
    return any(cost > window.calls for window in windows)


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
