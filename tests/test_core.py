import asyncio
from typing import Any, cast

import pytest

from pydecorators._core import (
    async_sleep,
    is_async_callable,
    mirror_metadata,
    monotonic,
    require_non_negative_number,
    require_positive_number,
    sync_sleep,
)
from pydecorators.exceptions import ConfigurationError


def sync_function() -> str:
    """A synchronous test function."""

    return "sync"


async def async_function() -> str:
    """An asynchronous test function."""

    return "async"


class AsyncCallableObject:
    async def __call__(self) -> str:
        return "async object"


def test_is_async_callable_detects_async_functions_and_callable_objects() -> None:
    assert not is_async_callable(sync_function)
    assert is_async_callable(async_function)
    assert is_async_callable(AsyncCallableObject())
    assert not is_async_callable(42)


def test_monotonic_increases() -> None:
    first = monotonic()
    second = monotonic()

    assert second >= first


def test_sync_sleep_accepts_zero_seconds() -> None:
    sync_sleep(0)


async def test_async_sleep_accepts_zero_seconds() -> None:
    await async_sleep(0)


def test_require_positive_number_accepts_positive_values() -> None:
    require_positive_number("attempts", 1)
    require_positive_number("delay", 0.1)


@pytest.mark.parametrize("value", [0, -1, -0.1])
def test_require_positive_number_rejects_zero_and_negative_values(value: float) -> None:
    with pytest.raises(ConfigurationError, match="attempts must be greater than zero"):
        require_positive_number("attempts", value)


def test_require_non_negative_number_accepts_zero_and_positive_values() -> None:
    require_non_negative_number("delay", 0)
    require_non_negative_number("delay", 0.1)


def test_require_non_negative_number_rejects_negative_values() -> None:
    with pytest.raises(ConfigurationError, match="delay must be zero or greater"):
        require_non_negative_number("delay", -0.1)


def test_mirror_metadata_preserves_wrapped_function_metadata() -> None:
    def original(value: int) -> int:
        """Original docstring."""

        return value

    def wrapper(value: int) -> int:
        return original(value)

    mirrored = mirror_metadata(wrapper, original)

    assert mirrored(3) == 3
    assert mirrored.__name__ == "original"
    assert mirrored.__doc__ == "Original docstring."
    assert mirrored.__module__ == __name__
    assert mirrored.__qualname__.endswith("original")
    assert mirrored.__annotations__ == {"value": int, "return": int}
    assert cast(Any, mirrored).__wrapped__ is original


def test_async_detection_survives_asyncio_run() -> None:
    assert asyncio.run(async_function()) == "async"
