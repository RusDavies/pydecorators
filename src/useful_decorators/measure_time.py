"""Execution-time measurement decorator."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from useful_decorators._core import is_async_callable, mirror_metadata, monotonic
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class TimingInfo:
    """Timing data emitted by ``@measure_time``."""

    function: str
    duration: float
    success: bool
    exception: BaseException | None = None


TimingCallback = Callable[[TimingInfo], object]
MetricsHook = Callable[[str, float, bool], object]


def measure_time(
    *,
    callback: TimingCallback | None = None,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
    metrics_hook: MetricsHook | None = None,
    clock: Callable[[], float] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Measure sync or async function execution time."""

    _validate_measure_time_config(
        callback=callback,
        logger=logger,
        level=level,
        metrics_hook=metrics_hook,
        clock=clock,
    )
    active_clock = clock or monotonic

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        active_logger = logger

        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                start = active_clock()
                try:
                    result = async_func(*args, **kwargs)
                    if hasattr(result, "__await__"):
                        result = await result
                except Exception as exc:
                    await _emit_timing_async(
                        callback=callback,
                        logger=active_logger,
                        level=level,
                        metrics_hook=metrics_hook,
                        info=TimingInfo(func.__qualname__, active_clock() - start, False, exc),
                    )
                    raise
                await _emit_timing_async(
                    callback=callback,
                    logger=active_logger,
                    level=level,
                    metrics_hook=metrics_hook,
                    info=TimingInfo(func.__qualname__, active_clock() - start, True),
                )
                return result

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = active_clock()
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                _emit_timing(
                    callback=callback,
                    logger=active_logger,
                    level=level,
                    metrics_hook=metrics_hook,
                    info=TimingInfo(func.__qualname__, active_clock() - start, False, exc),
                )
                raise
            _emit_timing(
                callback=callback,
                logger=active_logger,
                level=level,
                metrics_hook=metrics_hook,
                info=TimingInfo(func.__qualname__, active_clock() - start, True),
            )
            return result

        return mirror_metadata(wrapper, func)

    return decorate


def _validate_measure_time_config(
    *,
    callback: TimingCallback | None,
    logger: logging.Logger | None,
    level: int,
    metrics_hook: MetricsHook | None,
    clock: Callable[[], float] | None,
) -> None:
    if callback is not None and not callable(callback):
        raise ConfigurationError("callback must be callable when provided")
    if logger is not None and not isinstance(logger, logging.Logger):
        raise ConfigurationError("logger must be a logging.Logger when provided")
    if not isinstance(level, int):
        raise ConfigurationError("level must be an integer logging level")
    if metrics_hook is not None and not callable(metrics_hook):
        raise ConfigurationError("metrics_hook must be callable when provided")
    if clock is not None and not callable(clock):
        raise ConfigurationError("clock must be callable when provided")


def _emit_timing(
    *,
    callback: TimingCallback | None,
    logger: logging.Logger | None,
    level: int,
    metrics_hook: MetricsHook | None,
    info: TimingInfo,
) -> None:
    if callback is not None:
        callback(info)
    if logger is not None:
        logger.log(
            level,
            "%s completed in %.6g seconds success=%s",
            info.function,
            info.duration,
            info.success,
            extra={
                "useful_decorators_function": info.function,
                "useful_decorators_duration_seconds": info.duration,
                "useful_decorators_success": info.success,
            },
        )
    if metrics_hook is not None:
        metrics_hook(info.function, info.duration, info.success)


async def _emit_timing_async(
    *,
    callback: TimingCallback | None,
    logger: logging.Logger | None,
    level: int,
    metrics_hook: MetricsHook | None,
    info: TimingInfo,
) -> None:
    if callback is not None:
        result = callback(info)
        if inspect.isawaitable(result):
            await result
    if logger is not None:
        logger.log(
            level,
            "%s completed in %.6g seconds success=%s",
            info.function,
            info.duration,
            info.success,
            extra={
                "useful_decorators_function": info.function,
                "useful_decorators_duration_seconds": info.duration,
                "useful_decorators_success": info.success,
            },
        )
    if metrics_hook is not None:
        result = metrics_hook(info.function, info.duration, info.success)
        if inspect.isawaitable(result):
            await result
