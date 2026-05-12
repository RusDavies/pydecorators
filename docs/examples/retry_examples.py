"""Executable examples for @retry documentation."""

import asyncio

from useful_decorators import retry


def transient_success_example() -> tuple[str, list[float], list[int]]:
    """Retry a transient failure and inject sleep so the example stays fast."""

    attempts_seen: list[int] = []
    sleeps: list[float] = []
    failures_remaining = 1

    @retry(
        attempts=3,
        delay=0.25,
        exceptions=ConnectionError,
        before_attempt=attempts_seen.append,
        sleep=sleeps.append,
    )
    def call_service() -> str:
        nonlocal failures_remaining
        if failures_remaining:
            failures_remaining -= 1
            raise ConnectionError("temporary outage")
        return "ok"

    return call_service(), sleeps, attempts_seen


def predicate_example() -> str:
    """Retry only errors accepted by retry_if."""

    messages = iter(["transient overload", "permanent invalid request"])

    @retry(
        attempts=3,
        exceptions=RuntimeError,
        retry_if=lambda exc: "transient" in str(exc),
    )
    def run_job() -> str:
        raise RuntimeError(next(messages))

    try:
        run_job()
    except RuntimeError as exc:
        return str(exc)
    return "ok"


async def async_retry_example() -> tuple[str, list[float]]:
    """Use the same policy shape with async functions."""

    sleeps: list[float] = []
    failures_remaining = 1

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        await asyncio.sleep(0)

    @retry(attempts=3, delay=0.1, exceptions=TimeoutError, sleep=fake_sleep)
    async def fetch_user() -> str:
        nonlocal failures_remaining
        await asyncio.sleep(0)
        if failures_remaining:
            failures_remaining -= 1
            raise TimeoutError("slow dependency")
        return "user"

    return await fetch_user(), sleeps
