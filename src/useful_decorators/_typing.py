"""Shared typing primitives for decorator implementations."""

from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeAlias, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

SyncCallable: TypeAlias = Callable[P, R]
AsyncCallable: TypeAlias = Callable[P, Awaitable[R]]
AnyCallable: TypeAlias = Callable[..., Any]
Decorator: TypeAlias = Callable[[SyncCallable[P, R]], SyncCallable[P, R]]
