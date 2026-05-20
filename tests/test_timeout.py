import asyncio
from typing import Any

import pytest

from pydecorators import ConfigurationError, FunctionTimedOut, timeout


@pytest.mark.asyncio
async def test_timeout_allows_async_function_before_deadline() -> None:
    @timeout(seconds=1)
    async def quick() -> str:
        await asyncio.sleep(0)
        return "ok"

    assert await quick() == "ok"


@pytest.mark.asyncio
async def test_timeout_raises_function_timed_out_after_deadline() -> None:
    @timeout(seconds=0.01)
    async def slow() -> str:
        await asyncio.sleep(1)
        return "late"

    with pytest.raises(FunctionTimedOut, match=r"function timed out after 0\.01 seconds"):
        await slow()


@pytest.mark.asyncio
async def test_timeout_cancels_timed_out_coroutine() -> None:
    cancelled = asyncio.Event()

    @timeout(seconds=0.01)
    async def slow() -> None:
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    with pytest.raises(FunctionTimedOut):
        await slow()

    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_timeout_uses_custom_message_and_exception() -> None:
    class CustomTimeout(Exception):
        pass

    @timeout(seconds=0.01, message="too slow", exception=CustomTimeout)
    async def slow() -> None:
        await asyncio.sleep(1)

    with pytest.raises(CustomTimeout, match="too slow"):
        await slow()


def test_timeout_rejects_sync_functions_conservatively() -> None:
    with pytest.raises(ConfigurationError, match="async callables only"):

        @timeout(seconds=1)
        def sync_function() -> str:
            return "not supported"


def test_timeout_preserves_async_metadata() -> None:
    @timeout(seconds=1)
    async def documented(value: int) -> int:
        """Original docs."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"seconds": 0}, "seconds must be greater than zero"),
        ({"seconds": 1, "message": object()}, "message must be a string"),
        ({"seconds": 1, "exception": object}, "exception must be an Exception type"),
    ],
)
def test_timeout_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        timeout(**kwargs)
