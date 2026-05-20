"""Circuit breaker decorator."""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Any, cast

from pydecorators._core import is_async_callable, mirror_metadata, monotonic
from pydecorators._typing import P, R
from pydecorators.exceptions import ConfigurationError, UsefulDecoratorsError


class CircuitState(enum.Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True, slots=True)
class CircuitBreakerOpen(UsefulDecoratorsError):
    """Raised when a call is rejected because the circuit is open."""

    reset_after: float

    def __str__(self) -> str:
        return f"Circuit breaker is open; retry after {self.reset_after:.6g} seconds"


ExceptionFilter = Callable[[BaseException], bool]


def circuit_breaker(
    *,
    failure_threshold: int = 3,
    reset_timeout: float = 30.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    exception_filter: ExceptionFilter | None = None,
    clock: Callable[[], float] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Stop calling a failing dependency until a reset timeout elapses."""

    _validate_config(failure_threshold, reset_timeout, exceptions, exception_filter, clock)
    active_clock = clock or monotonic
    state = CircuitState.CLOSED
    failure_count = 0
    opened_at: float | None = None
    lock = RLock()

    def current_state() -> CircuitState:
        nonlocal state, opened_at
        with lock:
            if (
                state is CircuitState.OPEN
                and opened_at is not None
                and active_clock() - opened_at >= reset_timeout
            ):
                state = CircuitState.HALF_OPEN
            return state

    def reset_after() -> float | None:
        with lock:
            current = current_state()
            if current is not CircuitState.OPEN or opened_at is None:
                return None
            elapsed = active_clock() - opened_at
            return max(0.0, reset_timeout - elapsed)

    def before_call() -> None:
        with lock:
            current = current_state()
            if current is CircuitState.OPEN:
                assert opened_at is not None
                elapsed = active_clock() - opened_at
                raise CircuitBreakerOpen(max(0.0, reset_timeout - elapsed))

    def record_success() -> None:
        nonlocal state, failure_count, opened_at
        with lock:
            state = CircuitState.CLOSED
            failure_count = 0
            opened_at = None

    def record_failure(exc: BaseException) -> None:
        nonlocal state, failure_count, opened_at
        if not isinstance(exc, exceptions):
            return
        if exception_filter is not None and not exception_filter(exc):
            return
        with lock:
            if state is CircuitState.HALF_OPEN:
                state = CircuitState.OPEN
                failure_count = failure_threshold
                opened_at = active_clock()
                return
            failure_count += 1
            if failure_count >= failure_threshold:
                state = CircuitState.OPEN
                opened_at = active_clock()

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                before_call()
                try:
                    result = async_func(*args, **kwargs)
                    if hasattr(result, "__await__"):
                        result = await result
                except BaseException as exc:
                    record_failure(exc)
                    raise
                record_success()
                return result

            wrapped = mirror_metadata(
                cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func)
            )
            _attach_inspection(wrapped, current_state, reset_after)
            return wrapped

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            before_call()
            try:
                result = func(*args, **kwargs)
            except BaseException as exc:
                record_failure(exc)
                raise
            record_success()
            return result

        wrapped = mirror_metadata(wrapper, func)
        _attach_inspection(wrapped, current_state, reset_after)
        return wrapped

    return decorate


def _attach_inspection(
    wrapper: Callable[P, R],
    current_state: Callable[[], CircuitState],
    reset_after: Callable[[], float | None],
) -> None:
    wrapper.circuit_state = current_state  # type: ignore[attr-defined]
    wrapper.circuit_reset_after = reset_after  # type: ignore[attr-defined]


def _validate_config(
    failure_threshold: int,
    reset_timeout: float,
    exceptions: tuple[type[BaseException], ...],
    exception_filter: ExceptionFilter | None,
    clock: Callable[[], float] | None,
) -> None:
    if not isinstance(failure_threshold, int) or failure_threshold < 1:
        raise ConfigurationError("failure_threshold must be a positive integer")
    if not isinstance(reset_timeout, int | float) or reset_timeout <= 0:
        raise ConfigurationError("reset_timeout must be a positive number")
    if not isinstance(exceptions, tuple) or not exceptions:
        raise ConfigurationError("exceptions must be a non-empty tuple of exception types")
    if not all(isinstance(item, type) and issubclass(item, BaseException) for item in exceptions):
        raise ConfigurationError("exceptions must contain only exception types")
    if exception_filter is not None and not callable(exception_filter):
        raise ConfigurationError("exception_filter must be callable when provided")
    if clock is not None and not callable(clock):
        raise ConfigurationError("clock must be callable when provided")
