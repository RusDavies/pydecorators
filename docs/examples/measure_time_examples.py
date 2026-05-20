"""Executable examples for @measure_time documentation."""

import asyncio

from pydecorators import TimingInfo, measure_time


class ExampleClock:
    """Small controllable clock for deterministic timing examples."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def callback_example() -> tuple[str, TimingInfo]:
    """Collect TimingInfo objects with a callback."""

    clock = ExampleClock()
    timings: list[TimingInfo] = []

    @measure_time(callback=timings.append, clock=clock)
    def load_report() -> str:
        clock.advance(0.25)
        return "ready"

    result = load_report()
    return result, timings[0]


def metrics_hook_example() -> list[tuple[str, float, bool]]:
    """Feed simple metric observations from the timing hook."""

    clock = ExampleClock()
    observed: list[tuple[str, float, bool]] = []

    @measure_time(
        metrics_hook=lambda name, duration, success: observed.append((name, duration, success)),
        clock=clock,
    )
    def rebuild_cache() -> None:
        clock.advance(0.5)

    rebuild_cache()
    return observed


async def async_timing_example() -> TimingInfo:
    """Measure async functions with the same TimingInfo callback."""

    clock = ExampleClock()
    timings: list[TimingInfo] = []

    @measure_time(callback=timings.append, clock=clock)
    async def refresh_user() -> str:
        await asyncio.sleep(0)
        clock.advance(0.125)
        return "refreshed"

    await refresh_user()
    return timings[0]
