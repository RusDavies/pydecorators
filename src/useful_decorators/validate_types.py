"""Runtime type validation decorator."""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from typing import Annotated, Any, Literal, Union, cast, get_args, get_origin, get_type_hints

from useful_decorators._core import is_async_callable, mirror_metadata
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError, ValidationError

NoneType = type(None)


def validate_types(
    *,
    validate_return: bool = False,
    deep: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Validate annotated arguments, and optionally return values, at runtime."""

    if not isinstance(validate_return, bool):
        raise ConfigurationError("validate_return must be a boolean")
    if not isinstance(deep, bool):
        raise ConfigurationError("deep must be a boolean")

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(func)
        hints = get_type_hints(func)

        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                _validate_bound_arguments(func.__qualname__, signature, hints, args, kwargs, deep)
                result = async_func(*args, **kwargs)
                if hasattr(result, "__await__"):
                    result = await result
                _validate_return_value(func.__qualname__, hints, result, validate_return, deep)
                return result

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _validate_bound_arguments(func.__qualname__, signature, hints, args, kwargs, deep)
            result = func(*args, **kwargs)
            _validate_return_value(func.__qualname__, hints, result, validate_return, deep)
            return result

        return mirror_metadata(wrapper, func)

    return decorate


def _validate_bound_arguments(
    function_name: str,
    signature: inspect.Signature,
    hints: dict[str, object],
    args: tuple[object, ...],
    kwargs: dict[str, object],
    deep: bool,
) -> None:
    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()
    for name, value in bound.arguments.items():
        expected = hints.get(name)
        if expected is None:
            continue
        if not _matches_type(value, expected, deep=deep):
            raise ValidationError(
                f"{function_name}() argument {name!r} expected "
                f"{_format_type(expected)}, got {type(value).__name__}"
            )


def _validate_return_value(
    function_name: str,
    hints: dict[str, object],
    value: object,
    validate_return: bool,
    deep: bool,
) -> None:
    if not validate_return or "return" not in hints:
        return
    expected = hints["return"]
    if not _matches_type(value, expected, deep=deep):
        raise ValidationError(
            f"{function_name}() return value expected "
            f"{_format_type(expected)}, got {type(value).__name__}"
        )


def _matches_type(value: object, expected: object, *, deep: bool = False) -> bool:
    if expected is Any:
        return True
    if expected is None or expected is NoneType:
        return value is None
    origin = get_origin(expected)
    args = get_args(expected)

    if origin is Annotated:
        if not args:
            return True
        return _matches_type(value, args[0], deep=deep)
    if origin is Literal:
        return value in args
    if origin in {Union, types.UnionType}:
        return any(_matches_type(value, option, deep=deep) for option in args)
    if origin is list:
        return isinstance(value, list) and (
            not deep or not args or all(_matches_type(item, args[0], deep=True) for item in value)
        )
    if origin is dict:
        return isinstance(value, dict) and (
            not deep
            or len(args) != 2
            or all(
                _matches_type(key, args[0], deep=True) and _matches_type(item, args[1], deep=True)
                for key, item in value.items()
            )
        )
    if origin is tuple:
        return isinstance(value, tuple) and _matches_tuple(value, args, deep=deep)
    if origin is set:
        return isinstance(value, set) and (
            not deep or not args or all(_matches_type(item, args[0], deep=True) for item in value)
        )
    if origin is frozenset:
        return isinstance(value, frozenset) and (
            not deep or not args or all(_matches_type(item, args[0], deep=True) for item in value)
        )
    if isinstance(expected, type):
        return isinstance(value, expected)
    return True


def _matches_tuple(value: tuple[object, ...], args: tuple[object, ...], *, deep: bool) -> bool:
    if not deep or not args:
        return True
    if len(args) == 2 and args[1] is Ellipsis:
        return all(_matches_type(item, args[0], deep=True) for item in value)
    return len(value) == len(args) and all(
        _matches_type(item, expected, deep=True) for item, expected in zip(value, args, strict=True)
    )


def _format_type(expected: object) -> str:
    if expected is None or expected is NoneType:
        return "None"
    origin = get_origin(expected)
    if origin is Annotated:
        args = get_args(expected)
        return _format_type(args[0]) if args else "Annotated"
    if origin is Literal:
        values = ", ".join(repr(value) for value in get_args(expected))
        return f"Literal[{values}]"
    name = getattr(expected, "__name__", None)
    if isinstance(name, str):
        return name
    return str(expected).replace("typing.", "")
