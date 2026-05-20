import asyncio
from typing import Any

import pytest

from pydecorators import CircuitBreakerOpen, CircuitState, ConfigurationError, circuit_breaker


class MutableClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_circuit_breaker_opens_after_failure_threshold() -> None:
    clock = MutableClock()
    calls = 0

    @circuit_breaker(failure_threshold=2, reset_timeout=10, clock=clock)
    def flaky() -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        flaky()
    with pytest.raises(RuntimeError):
        flaky()
    with pytest.raises(CircuitBreakerOpen, match="retry after 10"):
        flaky()
    assert calls == 2


def test_circuit_breaker_half_open_success_closes_circuit() -> None:
    clock = MutableClock()
    should_fail = True

    @circuit_breaker(failure_threshold=1, reset_timeout=5, clock=clock)
    def service() -> str:
        if should_fail:
            raise RuntimeError("down")
        return "ok"

    with pytest.raises(RuntimeError):
        service()
    clock.advance(5)
    should_fail = False
    assert service() == "ok"
    assert service() == "ok"


def test_circuit_breaker_half_open_failure_reopens_circuit() -> None:
    clock = MutableClock()

    @circuit_breaker(failure_threshold=1, reset_timeout=5, clock=clock)
    def service() -> str:
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        service()
    clock.advance(5)
    with pytest.raises(RuntimeError):
        service()
    with pytest.raises(CircuitBreakerOpen, match="retry after 5"):
        service()


def test_circuit_breaker_exposes_state_inspection_helpers() -> None:
    clock = MutableClock()

    @circuit_breaker(failure_threshold=1, reset_timeout=5, clock=clock)
    def service() -> str:
        raise RuntimeError("down")

    circuit_state = service.circuit_state  # type: ignore[attr-defined]
    circuit_reset_after = service.circuit_reset_after  # type: ignore[attr-defined]

    assert circuit_state() is CircuitState.CLOSED
    assert circuit_reset_after() is None
    with pytest.raises(RuntimeError):
        service()
    assert circuit_state() is CircuitState.OPEN
    assert circuit_reset_after() == 5
    clock.advance(5)
    assert circuit_state() is CircuitState.HALF_OPEN
    assert circuit_reset_after() is None


def test_circuit_breaker_respects_exception_types_and_filters() -> None:
    clock = MutableClock()

    @circuit_breaker(
        failure_threshold=1,
        reset_timeout=5,
        exceptions=(ValueError,),
        exception_filter=lambda exc: "count" in str(exc),
        clock=clock,
    )
    def service(exc: BaseException) -> None:
        raise exc

    with pytest.raises(RuntimeError):
        service(RuntimeError("ignored"))
    with pytest.raises(ValueError):
        service(ValueError("ignored"))
    with pytest.raises(ValueError):
        service(ValueError("count this"))
    with pytest.raises(CircuitBreakerOpen):
        service(ValueError("count this"))


@pytest.mark.asyncio
async def test_circuit_breaker_supports_async_functions() -> None:
    clock = MutableClock()
    calls = 0

    @circuit_breaker(failure_threshold=1, reset_timeout=5, clock=clock)
    async def service() -> str:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        await service()
    with pytest.raises(CircuitBreakerOpen):
        await service()
    assert calls == 1


def test_circuit_breaker_preserves_metadata() -> None:
    @circuit_breaker()
    def documented() -> str:
        """Original docs."""
        return "ok"

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"failure_threshold": 0}, "failure_threshold must be a positive integer"),
        ({"reset_timeout": 0}, "reset_timeout must be a positive number"),
        ({"exceptions": ()}, "exceptions must be a non-empty tuple"),
        ({"exceptions": (object,)}, "exceptions must contain only exception types"),
        ({"exception_filter": object()}, "exception_filter must be callable"),
        ({"clock": object()}, "clock must be callable"),
    ],
)
def test_circuit_breaker_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        circuit_breaker(**kwargs)
