"""Runtime type validation decorator."""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from typing import Any, Union, cast, get_args, get_origin, get_type_hints

from useful_decorators._core import is_async_callable, mirror_metadata
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError, ValidationError

NoneType = type(None)


def validate_types(
    *,
    validate_return: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Validate annotated arguments, and optionally return values, at runtime."""

    if not isinstance(validate_return, bool):
        raise ConfigurationError("validate_return must be a boolean")

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(func)
        hints = get_type_hints(func)

        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                _validate_bound_arguments(func.__qualname__, signature, hints, args, kwargs)
                result = async_func(*args, **kwargs)
                if hasattr(result, "__await__"):
                    result = await result
                _validate_return_value(func.__qualname__, hints, result, validate_return)
                return result

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _validate_bound_arguments(func.__qualname__, signature, hints, args, kwargs)
            result = func(*args, **kwargs)
            _validate_return_value(func.__qualname__, hints, result, validate_return)
            return result

        return mirror_metadata(wrapper, func)

    return decorate


def _validate_bound_arguments(
    function_name: str,
    signature: inspect.Signature,
    hints: dict[str, object],
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()
    for name, value in bound.arguments.items():
        expected = hints.get(name)
        if expected is None:
            continue
        if not _matches_type(value, expected):
            raise ValidationError(
                f"{function_name}() argument {name!r} expected "
                f"{_format_type(expected)}, got {type(value).__name__}"
            )


def _validate_return_value(
    function_name: str,
    hints: dict[str, object],
    value: object,
    validate_return: bool,
) -> None:
    if not validate_return or "return" not in hints:
        return
    expected = hints["return"]
    if not _matches_type(value, expected):
        raise ValidationError(
            f"{function_name}() return value expected "
            f"{_format_type(expected)}, got {type(value).__name__}"
        )


def _matches_type(value: object, expected: object) -> bool:
    if expected is Any:
        return True
    if expected is None or expected is NoneType:
        return value is None
    origin = get_origin(expected)
    args = get_args(expected)

    if origin in {Union, types.UnionType}:
        return any(_matches_type(value, option) for option in args)
    if origin is list:
        return isinstance(value, list)
    if origin is dict:
        return isinstance(value, dict)
    if origin is tuple:
        return isinstance(value, tuple)
    if origin is set:
        return isinstance(value, set)
    if origin is frozenset:
        return isinstance(value, frozenset)
    if isinstance(expected, type):
        return isinstance(value, expected)
    return True


def _format_type(expected: object) -> str:
    if expected is None or expected is NoneType:
        return "None"
    name = getattr(expected, "__name__", None)
    if isinstance(name, str):
        return name
    return str(expected).replace("typing.", "")
