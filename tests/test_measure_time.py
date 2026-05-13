import asyncio
import logging
from typing import Any

import pytest

from useful_decorators import ConfigurationError, TimingInfo, measure_time


class MutableClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        current = self.now
        self.now += 0.5
        return current


def messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records]


def extra(record: logging.LogRecord, name: str) -> object:
    return record.__dict__[name]


def test_measure_time_calls_callback_for_sync_success() -> None:
    clock = MutableClock()
    timings: list[TimingInfo] = []

    @measure_time(callback=timings.append, clock=clock)
    def add(left: int, right: int) -> int:
        return left + right

    assert add(1, 2) == 3
    assert timings == [
        TimingInfo(
            function="test_measure_time_calls_callback_for_sync_success.<locals>.add",
            duration=0.5,
            success=True,
        )
    ]


def test_measure_time_calls_callback_for_sync_exception() -> None:
    clock = MutableClock()
    timings: list[TimingInfo] = []

    @measure_time(callback=timings.append, clock=clock)
    def broken() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        broken()

    assert len(timings) == 1
    assert timings[0].function.endswith("broken")
    assert timings[0].duration == 0.5
    assert timings[0].success is False
    assert isinstance(timings[0].exception, ValueError)


def test_measure_time_logs_duration(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.measure_time")
    clock = MutableClock()

    @measure_time(logger=logger, clock=clock)
    def work() -> str:
        return "ok"

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert work() == "ok"

    assert messages(caplog)[0].endswith("work completed in 0.5 seconds success=True")
    assert str(extra(caplog.records[0], "useful_decorators_function")).endswith("work")
    assert extra(caplog.records[0], "useful_decorators_duration_seconds") == 0.5
    assert extra(caplog.records[0], "useful_decorators_success") is True


def test_measure_time_calls_metrics_hook() -> None:
    clock = MutableClock()
    metrics: list[tuple[str, float, bool]] = []

    @measure_time(
        metrics_hook=lambda name, duration, success: metrics.append((name, duration, success)),
        clock=clock,
    )
    def work() -> str:
        return "ok"

    assert work() == "ok"
    assert len(metrics) == 1
    assert metrics[0][0].endswith("work")
    assert metrics[0][1:] == (0.5, True)


@pytest.mark.asyncio
async def test_measure_time_supports_async_functions() -> None:
    clock = MutableClock()
    timings: list[TimingInfo] = []

    @measure_time(callback=timings.append, clock=clock)
    async def async_work() -> str:
        await asyncio.sleep(0)
        return "ok"

    assert await async_work() == "ok"
    assert len(timings) == 1
    assert timings[0].function.endswith("async_work")
    assert timings[0].duration == 0.5
    assert timings[0].success is True


def test_measure_time_preserves_metadata() -> None:
    @measure_time()
    def documented(value: int) -> int:
        """Original docs."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"callback": object()}, "callback must be callable"),
        ({"logger": object()}, "logger must be a logging.Logger"),
        ({"level": "info"}, "level must be an integer"),
        ({"metrics_hook": object()}, "metrics_hook must be callable"),
        ({"clock": object()}, "clock must be callable"),
    ],
)
def test_measure_time_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        measure_time(**kwargs)
