"""Timeout decorator."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast

from useful_decorators._core import is_async_callable, mirror_metadata
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError, FunctionTimedOut


def timeout(
    *,
    seconds: float,
    message: str | None = None,
    exception: type[Exception] = FunctionTimedOut,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Fail an async callable if it does not complete before *seconds*."""

    _validate_timeout_config(seconds=seconds, message=message, exception=exception)

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        if not is_async_callable(func):
            raise ConfigurationError(
                "timeout currently supports async callables only; "
                "sync timeout behavior is intentionally not implemented"
            )

        async_func = cast(Callable[P, Any], func)

        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
            try:
                result = async_func(*args, **kwargs)
                if hasattr(result, "__await__"):
                    return await asyncio.wait_for(result, timeout=seconds)
                return result
            except TimeoutError as exc:
                raise exception(_timeout_message(message, seconds)) from exc

        return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

    return decorate


def _validate_timeout_config(
    *,
    seconds: float,
    message: str | None,
    exception: type[Exception],
) -> None:
    if seconds <= 0:
        raise ConfigurationError("seconds must be greater than zero")
    if message is not None and not isinstance(message, str):
        raise ConfigurationError("message must be a string when provided")
    if not isinstance(exception, type) or not issubclass(exception, Exception):
        raise ConfigurationError("exception must be an Exception type")


def _timeout_message(message: str | None, seconds: float) -> str:
    if message is not None:
        return message
    return f"function timed out after {seconds:g} seconds"
