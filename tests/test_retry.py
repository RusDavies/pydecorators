import asyncio
import importlib
from typing import Any

import pytest

from useful_decorators import ConfigurationError, retry


def test_retry_succeeds_after_transient_failure() -> None:
    calls = 0
    sleeps: list[float] = []

    @retry(attempts=3, delay=0.1, sleep=sleeps.append)
    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert calls == 2
    assert sleeps == [0.1]


def test_retry_reraises_after_exhausted_attempts() -> None:
    calls = 0
    sleeps: list[float] = []

    @retry(attempts=3, delay=0.1, sleep=sleeps.append)
    def always_fails() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("still broken")

    with pytest.raises(ValueError, match="still broken"):
        always_fails()

    assert calls == 3
    assert sleeps == [0.1, 0.1]


def test_retry_does_not_retry_non_matching_exception() -> None:
    calls = 0

    @retry(attempts=3, exceptions=ValueError, sleep=lambda seconds: None)
    def raises_type_error() -> None:
        nonlocal calls
        calls += 1
        raise TypeError("wrong family")

    with pytest.raises(TypeError, match="wrong family"):
        raises_type_error()

    assert calls == 1


def test_retry_uses_predicate_to_stop_retries() -> None:
    calls = 0

    @retry(
        attempts=3,
        exceptions=ValueError,
        retry_if=lambda exc: "retry" in str(exc),
        sleep=lambda seconds: None,
    )
    def sometimes_retryable() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("retry" if calls == 1 else "stop")

    with pytest.raises(ValueError, match="stop"):
        sometimes_retryable()

    assert calls == 2


def test_retry_calculates_backoff_and_max_delay() -> None:
    sleeps: list[float] = []

    @retry(attempts=4, delay=0.5, backoff=3, max_delay=2, sleep=sleeps.append)
    def always_fails() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        always_fails()

    assert sleeps == [0.5, 1.5, 2]


def test_retry_calls_attempt_hooks() -> None:
    before: list[int] = []
    after: list[tuple[int, str | None]] = []
    calls = 0

    def record_after(attempt: int, exc: BaseException | None) -> None:
        after.append((attempt, type(exc).__name__ if exc else None))

    @retry(
        attempts=2,
        before_attempt=before.append,
        after_attempt=record_after,
        sleep=lambda seconds: None,
    )
    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("first")
        return "ok"

    assert flaky() == "ok"
    assert before == [1, 2]
    assert after == [(1, "ValueError"), (2, None)]


@pytest.mark.asyncio
async def test_retry_supports_async_functions() -> None:
    calls = 0
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        await asyncio.sleep(0)

    @retry(attempts=3, delay=0.2, sleep=fake_sleep)
    async def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("not yet")
        return "ok"

    assert await flaky() == "ok"
    assert calls == 3
    assert sleeps == [0.2, 0.2]


def test_retry_preserves_metadata() -> None:
    @retry(attempts=1)
    def documented(value: int) -> int:
        """Original docs."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"attempts": 0}, "attempts must be greater than zero"),
        ({"attempts": 1, "delay": -1}, "delay must be zero or greater"),
        ({"attempts": 1, "backoff": 0.5}, "backoff must be greater than or equal to 1"),
        ({"attempts": 1, "max_delay": -1}, "max_delay must be zero or greater"),
        ({"attempts": 1, "jitter": -1}, "jitter must be zero or greater"),
        ({"attempts": 1, "exceptions": ()}, "exceptions must include"),
        ({"attempts": 1, "exceptions": (ValueError, object)}, "exceptions must be exception types"),
    ],
)
def test_retry_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        retry(**kwargs)


def test_retry_applies_deterministic_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    jitter_values = iter([0.25, 0.75])
    retry_module = importlib.import_module("useful_decorators.retry")

    monkeypatch.setattr(
        retry_module.random,
        "uniform",
        lambda start, stop: next(jitter_values),
    )

    @retry(attempts=3, delay=1.0, jitter=0.5, sleep=sleeps.append)
    def always_fails() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        always_fails()

    assert sleeps == [1.25, 1.75]


@pytest.mark.asyncio
async def test_retry_applies_deterministic_jitter_for_async_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    jitter_values = iter([0.1, 0.2])

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    retry_module = importlib.import_module("useful_decorators.retry")
    monkeypatch.setattr(
        retry_module.random,
        "uniform",
        lambda start, stop: next(jitter_values),
    )

    @retry(attempts=3, delay=0.5, jitter=0.3, sleep=fake_sleep)
    async def always_fails() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await always_fails()

    assert sleeps == [0.6, 0.7]
