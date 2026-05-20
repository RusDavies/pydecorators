"""Shared typing primitives for decorator implementations."""

from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, Protocol, TypeAlias, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

SyncCallable: TypeAlias = Callable[P, R]
AsyncCallable: TypeAlias = Callable[P, Awaitable[R]]
AnyCallable: TypeAlias = Callable[..., Any]
Decorator: TypeAlias = Callable[[SyncCallable[P, R]], SyncCallable[P, R]]


class Clock(Protocol):
    """Callable protocol for injectable monotonic clocks."""

    def __call__(self) -> float: ...


class SyncSleep(Protocol):
    """Callable protocol for injectable synchronous sleep functions."""

    def __call__(self, seconds: float) -> None: ...


class AsyncSleep(Protocol):
    """Callable protocol for injectable asynchronous sleep functions."""

    def __call__(self, seconds: float) -> Awaitable[None]: ...
