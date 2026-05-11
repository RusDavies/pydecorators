from typing import Any, cast

import pytest

from useful_decorators import deprecated
from useful_decorators.exceptions import ConfigurationError


def test_deprecated_bare_usage_warns_and_returns_value() -> None:
    @deprecated
    def old_function(value: int) -> int:
        """Old function."""

        return value + 1

    with pytest.warns(DeprecationWarning, match="old_function is deprecated"):
        assert old_function(1) == 2


def test_deprecated_configured_usage_warns_with_full_message() -> None:
    @deprecated(
        "Kept for compatibility.",
        replacement="new_function",
        version="0.1.0",
        remove_in="1.0.0",
    )
    def old_function() -> str:
        return "ok"

    expected = (
        "old_function is deprecated since version 0.1.0 "
        "and will be removed in version 1.0.0. "
        "Use new_function instead. Kept for compatibility."
    )
    with pytest.warns(DeprecationWarning, match=expected):
        assert old_function() == "ok"


async def test_deprecated_async_function_warns_and_returns_value() -> None:
    @deprecated(replacement="new_async_function")
    async def old_async_function() -> str:
        return "ok"

    with pytest.warns(
        DeprecationWarning,
        match="old_async_function is deprecated. Use new_async_function instead.",
    ):
        assert await old_async_function() == "ok"


def test_deprecated_preserves_function_metadata() -> None:
    @deprecated("metadata test")
    def old_function(value: int) -> int:
        """Old function docstring."""

        return value

    assert old_function.__name__ == "old_function"
    assert old_function.__doc__ == "Old function docstring."
    assert old_function.__module__ == __name__
    assert old_function.__qualname__.endswith("old_function")
    assert old_function.__annotations__ == {"value": int, "return": int}
    assert cast(Any, old_function).__wrapped__ is not None


def test_deprecated_supports_custom_warning_category() -> None:
    class CustomDeprecationWarning(Warning):
        pass

    @deprecated(category=CustomDeprecationWarning)
    def old_function() -> str:
        return "ok"

    with pytest.warns(CustomDeprecationWarning, match="old_function is deprecated"):
        assert old_function() == "ok"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"reason": ""}, "reason must not be empty"),
        ({"replacement": ""}, "replacement must not be empty"),
        ({"version": ""}, "version must not be empty"),
        ({"remove_in": ""}, "remove_in must not be empty"),
        ({"stacklevel": 0}, "stacklevel must be greater than zero"),
    ],
)
def test_deprecated_rejects_invalid_configuration(kwargs: dict[str, object], match: str) -> None:
    with pytest.raises(ConfigurationError, match=match):
        deprecated(**kwargs)  # type: ignore[call-overload]


def test_deprecated_rejects_non_warning_category() -> None:
    with pytest.raises(ConfigurationError, match="category must be a Warning subclass"):
        deprecated(category=Exception)  # type: ignore[arg-type]
