"""Executable examples for @circuit_breaker documentation."""

import asyncio
from contextlib import suppress

from useful_decorators import CircuitBreakerOpen, circuit_breaker


class ExampleClock:
    """Small controllable clock for deterministic circuit-breaker examples."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def open_circuit_example() -> str:
    """Open the circuit after repeated dependency failures."""

    @circuit_breaker(failure_threshold=1, reset_timeout=30)
    def call_vendor() -> str:
        raise TimeoutError("vendor timed out")

    with suppress(TimeoutError):
        call_vendor()

    try:
        call_vendor()
    except CircuitBreakerOpen:
        return "fallback"
    return "called"


def half_open_recovery_example() -> list[str]:
    """Allow a successful half-open probe after the reset timeout."""

    clock = ExampleClock()
    responses = iter([TimeoutError("down"), "ok", "ok"])
    events: list[str] = []

    @circuit_breaker(failure_threshold=1, reset_timeout=10, clock=clock)
    def call_vendor() -> str:
        response = next(responses)
        if isinstance(response, BaseException):
            raise response
        return response

    with suppress(TimeoutError):
        call_vendor()
    with suppress(CircuitBreakerOpen):
        call_vendor()
        events.append("unexpected-call")

    clock.advance(10)
    events.append(call_vendor())
    events.append(call_vendor())
    return events


async def async_circuit_breaker_example() -> str:
    """Use the same circuit-breaker behavior with async functions."""

    @circuit_breaker(failure_threshold=1, reset_timeout=30)
    async def refresh_user() -> str:
        await asyncio.sleep(0)
        raise ConnectionError("dependency unavailable")

    with suppress(ConnectionError):
        await refresh_user()

    try:
        await refresh_user()
    except CircuitBreakerOpen:
        return "async fallback"
    return "called"
