"""Deprecation decorator."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any, cast, overload

from pydecorators._core import is_async_callable, mirror_metadata
from pydecorators._typing import P, R
from pydecorators.exceptions import ConfigurationError


def _build_deprecation_message(
    function_name: str,
    *,
    reason: str | None,
    replacement: str | None,
    version: str | None,
    remove_in: str | None,
) -> str:
    parts = [f"{function_name} is deprecated"]
    if version is not None:
        parts.append(f"since version {version}")
    if remove_in is not None:
        parts.append(f"and will be removed in version {remove_in}")

    message = " ".join(parts) + "."
    if replacement is not None:
        message += f" Use {replacement} instead."
    if reason is not None:
        message += f" {reason}"
    return message


def _validate_deprecated_config(
    *,
    reason: str | None,
    replacement: str | None,
    version: str | None,
    remove_in: str | None,
    category: type[Warning],
    stacklevel: int,
) -> None:
    for name, value in {
        "reason": reason,
        "replacement": replacement,
        "version": version,
        "remove_in": remove_in,
    }.items():
        if value is not None and not value.strip():
            raise ConfigurationError(f"{name} must not be empty")
    if not issubclass(category, Warning):
        raise ConfigurationError("category must be a Warning subclass")
    if stacklevel < 1:
        raise ConfigurationError("stacklevel must be greater than zero")


@overload
def deprecated(func: Callable[P, R], /) -> Callable[P, R]: ...


@overload
def deprecated(
    reason: str | None = None,
    *,
    replacement: str | None = None,
    version: str | None = None,
    remove_in: str | None = None,
    category: type[Warning] = DeprecationWarning,
    stacklevel: int = 2,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def deprecated(
    reason: Callable[P, R] | str | None = None,
    *,
    replacement: str | None = None,
    version: str | None = None,
    remove_in: str | None = None,
    category: type[Warning] = DeprecationWarning,
    stacklevel: int = 2,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Mark a function as deprecated.

    Supports both bare and configured usage::

        @deprecated
        def old_function(): ...

        @deprecated("Kept for compatibility.", replacement="new_function")
        def old_function(): ...
    """

    if callable(reason):
        func = reason
        _validate_deprecated_config(
            reason=None,
            replacement=replacement,
            version=version,
            remove_in=remove_in,
            category=category,
            stacklevel=stacklevel,
        )
        return _decorate_deprecated(
            func,
            reason=None,
            replacement=replacement,
            version=version,
            remove_in=remove_in,
            category=category,
            stacklevel=stacklevel,
        )

    _validate_deprecated_config(
        reason=reason,
        replacement=replacement,
        version=version,
        remove_in=remove_in,
        category=category,
        stacklevel=stacklevel,
    )

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return _decorate_deprecated(
            func,
            reason=reason,
            replacement=replacement,
            version=version,
            remove_in=remove_in,
            category=category,
            stacklevel=stacklevel,
        )

    return decorator


def _decorate_deprecated(
    func: Callable[P, R],
    *,
    reason: str | None,
    replacement: str | None,
    version: str | None,
    remove_in: str | None,
    category: type[Warning],
    stacklevel: int,
) -> Callable[P, R]:
    message = _build_deprecation_message(
        func.__name__,
        reason=reason,
        replacement=replacement,
        version=version,
        remove_in=remove_in,
    )

    if is_async_callable(func):
        async_func = cast(Callable[P, Any], func)

        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            warnings.warn(message, category, stacklevel=stacklevel)
            return await async_func(*args, **kwargs)

        return cast(Callable[P, R], mirror_metadata(async_wrapper, async_func))

    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        warnings.warn(message, category, stacklevel=stacklevel)
        return func(*args, **kwargs)

    return mirror_metadata(sync_wrapper, func)
