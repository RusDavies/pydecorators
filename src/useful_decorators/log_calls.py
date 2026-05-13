"""Call logging decorator."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from typing import Any, cast

from useful_decorators._core import is_async_callable, mirror_metadata, monotonic
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError

ResultSummarizer = Callable[[object], object]


def log_calls(
    *,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
    include_args: bool = False,
    include_result: bool = False,
    redact_args: Iterable[str] = (),
    summarize_result: ResultSummarizer | None = None,
    log_exceptions: bool = True,
    clock: Callable[[], float] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Log function calls, duration, optional arguments/results, and exceptions."""

    redacted_names = _validate_log_calls_config(
        level=level,
        redact_args=redact_args,
        summarize_result=summarize_result,
        clock=clock,
    )
    active_clock = clock or monotonic

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        active_logger = logger or logging.getLogger(func.__module__)

        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                start = active_clock()
                _log_started(
                    active_logger,
                    level,
                    func.__qualname__,
                    include_args=include_args,
                    redacted_names=redacted_names,
                    args=args,
                    kwargs=kwargs,
                )
                try:
                    result = async_func(*args, **kwargs)
                    if hasattr(result, "__await__"):
                        result = await result
                except Exception:
                    duration = active_clock() - start
                    if log_exceptions:
                        active_logger.exception(
                            "%s failed after %.6g seconds",
                            func.__qualname__,
                            duration,
                            extra=_log_extra(
                                func.__qualname__,
                                event="failed",
                                duration=duration,
                                success=False,
                            ),
                        )
                    raise
                duration = active_clock() - start
                _log_finished(
                    active_logger,
                    level,
                    func.__qualname__,
                    duration,
                    include_result=include_result,
                    summarize_result=summarize_result,
                    result=result,
                )
                return result

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = active_clock()
            _log_started(
                active_logger,
                level,
                func.__qualname__,
                include_args=include_args,
                redacted_names=redacted_names,
                args=args,
                kwargs=kwargs,
            )
            try:
                result = func(*args, **kwargs)
            except Exception:
                duration = active_clock() - start
                if log_exceptions:
                    active_logger.exception(
                        "%s failed after %.6g seconds",
                        func.__qualname__,
                        duration,
                        extra=_log_extra(
                            func.__qualname__,
                            event="failed",
                            duration=duration,
                            success=False,
                        ),
                    )
                raise
            duration = active_clock() - start
            _log_finished(
                active_logger,
                level,
                func.__qualname__,
                duration,
                include_result=include_result,
                summarize_result=summarize_result,
                result=result,
            )
            return result

        return mirror_metadata(wrapper, func)

    return decorate


def _validate_log_calls_config(
    *,
    level: int,
    redact_args: Iterable[str],
    summarize_result: ResultSummarizer | None,
    clock: Callable[[], float] | None,
) -> frozenset[str]:
    if not isinstance(level, int):
        raise ConfigurationError("level must be an integer logging level")
    try:
        redacted_names = frozenset(redact_args)
    except TypeError as exc:
        raise ConfigurationError("redact_args must be an iterable of argument names") from exc
    if not all(isinstance(name, str) for name in redacted_names):
        raise ConfigurationError("redact_args must contain only argument names")
    if summarize_result is not None and not callable(summarize_result):
        raise ConfigurationError("summarize_result must be callable when provided")
    if clock is not None and not callable(clock):
        raise ConfigurationError("clock must be callable when provided")
    return redacted_names


def _log_started(
    logger: logging.Logger,
    level: int,
    name: str,
    *,
    include_args: bool,
    redacted_names: frozenset[str],
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    if not include_args:
        logger.log(level, "%s started", name, extra=_log_extra(name, event="started"))
        return
    logger.log(
        level,
        "%s started args=%r kwargs=%r",
        name,
        args,
        _redact_kwargs(kwargs, redacted_names),
        extra=_log_extra(name, event="started"),
    )


def _log_finished(
    logger: logging.Logger,
    level: int,
    name: str,
    duration: float,
    *,
    include_result: bool,
    summarize_result: ResultSummarizer | None,
    result: object,
) -> None:
    if not include_result:
        logger.log(
            level,
            "%s finished in %.6g seconds",
            name,
            duration,
            extra=_log_extra(name, event="finished", duration=duration, success=True),
        )
        return
    summary = summarize_result(result) if summarize_result else result
    logger.log(
        level,
        "%s finished in %.6g seconds result=%r",
        name,
        duration,
        summary,
        extra=_log_extra(name, event="finished", duration=duration, success=True),
    )


def _log_extra(
    name: str,
    *,
    event: str,
    duration: float | None = None,
    success: bool | None = None,
) -> dict[str, object]:
    extra: dict[str, object] = {
        "useful_decorators_function": name,
        "useful_decorators_event": event,
    }
    if duration is not None:
        extra["useful_decorators_duration_seconds"] = duration
    if success is not None:
        extra["useful_decorators_success"] = success
    return extra


def _redact_kwargs(kwargs: dict[str, object], redacted_names: frozenset[str]) -> dict[str, object]:
    return {
        name: "<redacted>" if name in redacted_names else value for name, value in kwargs.items()
    }
