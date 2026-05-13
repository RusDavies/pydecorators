"""Rate limiting decorator."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Hashable
from threading import RLock
from typing import Any, Literal, cast

from useful_decorators._core import (
    async_sleep,
    is_async_callable,
    mirror_metadata,
    monotonic,
    sync_sleep,
)
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError, RateLimitExceeded

RateLimitMode = Literal["raise", "block"]
RateLimitKey = Callable[..., Hashable]


def rate_limit(
    *,
    calls: int,
    period: float,
    key: RateLimitKey | None = None,
    mode: RateLimitMode = "raise",
    clock: Callable[[], float] | None = None,
    sleep: Callable[[float], object] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Limit calls to a sync or async callable over a sliding time window."""

    _validate_rate_limit_config(calls=calls, period=period, key=key, mode=mode)
    limiter = _SlidingWindowLimiter(calls=calls, period=period, clock=clock or monotonic)

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
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
            window = self._windows[key]
            self._prune(window, now)
            if len(window) < self._calls:
                window.append(now)
                return None
            oldest = window[0]
            return max(0.0, oldest + self._period - now)

    def _prune(self, window: deque[float], now: float) -> None:
        cutoff = now - self._period
        while window and window[0] <= cutoff:
            window.popleft()


def _validate_rate_limit_config(
    *,
    calls: int,
    period: float,
    key: RateLimitKey | None,
    mode: RateLimitMode,
) -> None:
    if calls <= 0:
        raise ConfigurationError("calls must be greater than zero")
    if period <= 0:
        raise ConfigurationError("period must be greater than zero")
    if key is not None and not callable(key):
        raise ConfigurationError("key must be callable when provided")
    if mode not in {"raise", "block"}:
        raise ConfigurationError('mode must be "raise" or "block"')


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
