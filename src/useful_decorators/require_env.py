"""Environment variable requirement decorator."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from useful_decorators._core import is_async_callable, mirror_metadata
from useful_decorators._typing import P, R
from useful_decorators.exceptions import ConfigurationError

EnvValidator = Callable[[str], bool | None]


@dataclass(frozen=True, slots=True)
class EnvRequirementError(RuntimeError):
    """Raised when a required environment variable is missing or invalid."""

    variable: str
    reason: str

    def __str__(self) -> str:
        return f"Environment variable {self.variable!r} {self.reason}"


def require_env(
    *names: str,
    validators: Mapping[str, EnvValidator] | None = None,
    environ: Mapping[str, str] | None = None,
    messages: Mapping[str, str] | None = None,
    allow_empty: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Require environment variables to exist and optionally pass validators at call time."""

    requirements = _normalize_names(names)
    active_validators = dict(validators or {})
    active_messages = dict(messages or {})
    _validate_config(requirements, active_validators, environ, active_messages, allow_empty)

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                _check_environment(
                    requirements,
                    active_validators,
                    environ,
                    active_messages,
                    allow_empty,
                )
                result = async_func(*args, **kwargs)
                if hasattr(result, "__await__"):
                    return await result
                return result

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _check_environment(
                requirements,
                active_validators,
                environ,
                active_messages,
                allow_empty,
            )
            return func(*args, **kwargs)

        return mirror_metadata(wrapper, func)

    return decorate


def _normalize_names(names: tuple[str, ...]) -> tuple[str, ...]:
    if len(names) == 1 and isinstance(names[0], str) and "," in names[0]:
        return tuple(part.strip() for part in names[0].split(",") if part.strip())
    return names


def _validate_config(
    names: Iterable[str],
    validators: Mapping[str, EnvValidator],
    environ: Mapping[str, str] | None,
    messages: Mapping[str, str],
    allow_empty: bool,
) -> None:
    names_tuple = tuple(names)
    if not names_tuple:
        raise ConfigurationError("require_env needs at least one variable name")
    for name in names_tuple:
        if not isinstance(name, str) or not name:
            raise ConfigurationError("environment variable names must be non-empty strings")
    for name, validator in validators.items():
        if name not in names_tuple:
            raise ConfigurationError(f"validator configured for unknown variable {name!r}")
        if not callable(validator):
            raise ConfigurationError(f"validator for {name!r} must be callable")
    if environ is not None and not isinstance(environ, Mapping):
        raise ConfigurationError("environ must be a mapping when provided")
    if not isinstance(allow_empty, bool):
        raise ConfigurationError("allow_empty must be a boolean")
    for name, message in messages.items():
        if name not in names_tuple:
            raise ConfigurationError(f"message configured for unknown variable {name!r}")
        if not isinstance(message, str) or not message:
            raise ConfigurationError(f"message for {name!r} must be a non-empty string")


def _check_environment(
    names: tuple[str, ...],
    validators: Mapping[str, EnvValidator],
    environ: Mapping[str, str] | None,
    messages: Mapping[str, str],
    allow_empty: bool,
) -> None:
    source = os.environ if environ is None else environ
    for name in names:
        if name not in source:
            raise EnvRequirementError(name, messages.get(name, "is required"))
        value = source[name]
        if not allow_empty and value == "":
            raise EnvRequirementError(name, "must not be empty")
        validator = validators.get(name)
        if validator is None:
            continue
        try:
            valid = validator(value)
        except Exception as exc:
            raise EnvRequirementError(name, "failed validation") from exc
        if valid is False:
            raise EnvRequirementError(name, "failed validation")
