import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from useful_decorators import ConfigurationError, RateLimitExceeded, rate_limit


class MutableClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_rate_limit_allows_calls_within_window() -> None:
    clock = MutableClock()
    calls = 0

    @rate_limit(calls=2, period=10, clock=clock)
    def limited() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    assert limited() == "ok"
    assert limited() == "ok"
    assert calls == 2


def test_rate_limit_raise_mode_rejects_exceeded_calls() -> None:
    clock = MutableClock()

    @rate_limit(calls=1, period=10, clock=clock)
    def limited() -> str:
        return "ok"

    assert limited() == "ok"
    with pytest.raises(RateLimitExceeded, match="retry after 10"):
        limited()


def test_rate_limit_sliding_window_resets_after_period() -> None:
    clock = MutableClock()

    @rate_limit(calls=1, period=10, clock=clock)
    def limited() -> str:
        return "ok"

    assert limited() == "ok"
    clock.advance(9.9)
    with pytest.raises(RateLimitExceeded):
        limited()
    clock.advance(0.1)
    assert limited() == "ok"


def test_rate_limit_sync_callers_share_bucket_across_threads() -> None:
    clock = MutableClock()

    @rate_limit(calls=2, period=10, clock=clock)
    def limited(value: int) -> int:
        return value

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(limited, value) for value in range(3)]

    successes = sorted(future.result() for future in futures if future.exception() is None)
    failures = [future.exception() for future in futures if future.exception() is not None]

    assert successes == [0, 1]
    assert len(failures) == 1
    assert isinstance(failures[0], RateLimitExceeded)


def test_rate_limit_key_isolates_buckets() -> None:
    clock = MutableClock()

    @rate_limit(calls=1, period=10, key=lambda tenant: tenant, clock=clock)
    def limited(tenant: str) -> str:
        return tenant

    assert limited("a") == "a"
    assert limited("b") == "b"
    with pytest.raises(RateLimitExceeded):
        limited("a")


def test_rate_limit_block_mode_sleeps_until_slot_available() -> None:
    clock = MutableClock()
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    @rate_limit(calls=1, period=10, mode="block", clock=clock, sleep=fake_sleep)
    def limited() -> str:
        return "ok"

    assert limited() == "ok"
    assert limited() == "ok"
    assert sleeps == [10]


@pytest.mark.asyncio
async def test_rate_limit_supports_async_raise_mode() -> None:
    clock = MutableClock()

    @rate_limit(calls=1, period=10, clock=clock)
    async def limited() -> str:
        await asyncio.sleep(0)
        return "ok"

    assert await limited() == "ok"
    with pytest.raises(RateLimitExceeded):
        await limited()


@pytest.mark.asyncio
async def test_rate_limit_supports_async_block_mode() -> None:
    clock = MutableClock()
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)
        await asyncio.sleep(0)

    @rate_limit(calls=1, period=5, mode="block", clock=clock, sleep=fake_sleep)
    async def limited() -> str:
        return "ok"

    assert await limited() == "ok"
    assert await limited() == "ok"
    assert sleeps == [5]


def test_rate_limit_preserves_metadata() -> None:
    @rate_limit(calls=1, period=1)
    def documented(value: int) -> int:
        """Original docs."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"calls": 0, "period": 1}, "calls must be greater than zero"),
        ({"calls": 1, "period": 0}, "period must be greater than zero"),
        ({"calls": 1, "period": 1, "key": object()}, "key must be callable"),
        ({"calls": 1, "period": 1, "mode": "wait"}, "mode must"),
    ],
)
def test_rate_limit_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        rate_limit(**kwargs)
