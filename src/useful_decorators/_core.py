"""Internal helpers shared by decorator implementations."""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeGuard, cast

from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError


def is_async_callable(func: object) -> TypeGuard[Callable[..., Awaitable[Any]]]:
    """Return whether *func* is an async callable.

    `inspect.iscoroutinefunction` handles normal async functions. The `__call__`
    fallback lets callable objects participate without each decorator needing to
    remember that Python allows functions to wear fake moustaches.
    """

    if inspect.iscoroutinefunction(func):
        return True
    if not callable(func):
        return False
    return inspect.iscoroutinefunction(type(func).__call__)


def monotonic() -> float:
    """Return a monotonic timestamp suitable for elapsed-time calculations."""

    return time.monotonic()


def sync_sleep(seconds: float) -> None:
    """Sleep synchronously for *seconds*. Exists mainly for injection in tests."""

    time.sleep(seconds)


async def async_sleep(seconds: float) -> None:
    """Sleep asynchronously for *seconds*. Exists mainly for injection in tests."""

    await asyncio.sleep(seconds)


def require_positive_number(name: str, value: float | int) -> None:
    """Raise :class:`ConfigurationError` unless *value* is greater than zero."""

    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")


def require_non_negative_number(name: str, value: float | int) -> None:
    """Raise :class:`ConfigurationError` unless *value* is zero or greater."""

    if value < 0:
        raise ConfigurationError(f"{name} must be zero or greater")


def mirror_metadata(wrapper: Callable[P, R], wrapped: Callable[P, R]) -> Callable[P, R]:
    """Apply standard wrapped-function metadata to *wrapper*.

    This is a tiny wrapper around :func:`functools.wraps` so decorators can use a
    single convention and tests can assert the convention once.
    """

    return cast(Callable[P, R], wraps(wrapped)(wrapper))
