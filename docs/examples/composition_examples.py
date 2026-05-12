"""Executable examples for decorator-composition documentation."""

import asyncio
import logging

from useful_decorators import (
    CircuitBreakerOpen,
    FunctionTimedOut,
    TimingInfo,
    circuit_breaker,
    log_calls,
    measure_time,
    retry,
    timeout,
)


class ExampleClock:
    """Small controllable clock for deterministic composition examples."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _example_logger() -> tuple[logging.Logger, _ListHandler]:
    logger = logging.getLogger("docs.composition")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = _ListHandler()
    logger.addHandler(handler)
    return logger, handler


def measure_whole_operation_example() -> tuple[str, int, float]:
    """Measure a full retrying operation as one logical call."""

    clock = ExampleClock()
    timings: list[TimingInfo] = []
    sleeps: list[float] = []
    failures_remaining = 1

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    @measure_time(callback=timings.append, clock=clock)
    @retry(attempts=2, delay=0.5, exceptions=ConnectionError, sleep=fake_sleep)
    def fetch_user() -> str:
        nonlocal failures_remaining
        clock.advance(0.25)
        if failures_remaining:
            failures_remaining -= 1
            raise ConnectionError("transient")
        return "user"

    result = fetch_user()
    return result, len(timings), timings[0].duration


def log_one_logical_call_example() -> list[str]:
    """Log one outer call while retry handles internal attempts."""

    logger, handler = _example_logger()
    failures_remaining = 1

    @log_calls(logger=logger)
    @retry(attempts=2, exceptions=ConnectionError, sleep=lambda seconds: None)
    def call_api() -> str:
        nonlocal failures_remaining
        if failures_remaining:
            failures_remaining -= 1
            raise ConnectionError("temporary")
        return "ok"

    call_api()
    return handler.messages


def circuit_outside_retry_example() -> str:
    """Open the circuit only after retries are exhausted."""

    @circuit_breaker(failure_threshold=1, reset_timeout=30)
    @retry(attempts=2, exceptions=ConnectionError, sleep=lambda seconds: None)
    def call_api() -> str:
        raise ConnectionError("still down")

    for _ in range(2):
        try:
            call_api()
        except (ConnectionError, CircuitBreakerOpen) as exc:
            if isinstance(exc, CircuitBreakerOpen):
                return "open after one logical failure"
    return "closed"


async def timeout_outside_retry_example() -> str:
    """Apply one async timeout budget around the whole retrying operation."""

    @timeout(seconds=0.01)
    @retry(attempts=3, exceptions=TimeoutError)
    async def fetch_user() -> str:
        await asyncio.sleep(1)
        return "user"

    try:
        await fetch_user()
    except FunctionTimedOut:
        return "whole operation timed out"
    return "finished"
