"""Dogfood scenarios for blakemere-decorators installed wheel.

This module intentionally runs outside the normal test suite source imports when
invoked through scripts/dogfood_local_wheel.py.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

from useful_decorators import (
    CircuitBreakerOpen,
    circuit_breaker,
    log_calls,
    measure_time,
    rate_limit,
    require_env,
    retry,
    timeout,
    validate_types,
)

logger = logging.getLogger("dogfood.service_client")


@dataclass(slots=True)
class DogfoodResult:
    sync_payload: str
    async_payload: str
    timings: int
    attempts: int
    breaker_opened: bool


class VendorClient:
    def __init__(self) -> None:
        self.sync_attempts = 0
        self.breaker_attempts = 0
        self.timings: list[object] = []

    @measure_time(callback=lambda info: VendorClient._record_timing(info))
    @log_calls(logger=logger, include_args=True, redact_args={"token"})
    @require_env("DOGFOOD_API_TOKEN")
    @rate_limit(calls=5, period=60)
    @retry(attempts=3, delay=0)
    @validate_types(validate_return=True)
    def fetch_sync(self, customer_id: str, *, token: str) -> str:
        self.sync_attempts += 1
        if self.sync_attempts < 2:
            raise ConnectionError("transient dogfood failure")
        return f"sync:{customer_id}:{len(token)}"

    @circuit_breaker(failure_threshold=2, reset_timeout=60)
    def flaky_dependency(self) -> str:
        self.breaker_attempts += 1
        raise TimeoutError("dependency down")

    @staticmethod
    def _record_timing(info: object) -> None:
        # The callback is deliberately lightweight: dogfood verifies that an
        # installed package can call it, not that metrics plumbing is fancy.
        _TIMINGS.append(info)


_TIMINGS: list[object] = []


@timeout(seconds=1)
@log_calls(logger=logger)
@validate_types(validate_return=True)
async def fetch_async(customer_id: str) -> str:
    await asyncio.sleep(0)
    return f"async:{customer_id}"


async def run_async_scenario() -> str:
    return await fetch_async("customer-123")


def run_sync_scenario() -> tuple[str, int, bool]:
    os.environ.setdefault("DOGFOOD_API_TOKEN", "dogfood-secret")
    client = VendorClient()
    payload = client.fetch_sync("customer-123", token=os.environ["DOGFOOD_API_TOKEN"])

    breaker_opened = False
    for _ in range(3):
        try:
            client.flaky_dependency()
        except CircuitBreakerOpen:
            breaker_opened = True
        except TimeoutError:
            pass

    return payload, client.sync_attempts, breaker_opened


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    sync_payload, attempts, breaker_opened = run_sync_scenario()
    async_payload = asyncio.run(run_async_scenario())
    result = DogfoodResult(
        sync_payload=sync_payload,
        async_payload=async_payload,
        timings=len(_TIMINGS),
        attempts=attempts,
        breaker_opened=breaker_opened,
    )
    if result.sync_payload != "sync:customer-123:14":
        raise SystemExit(f"unexpected sync payload: {result.sync_payload}")
    if result.async_payload != "async:customer-123":
        raise SystemExit(f"unexpected async payload: {result.async_payload}")
    if result.attempts != 2:
        raise SystemExit(f"retry did not produce expected attempts: {result.attempts}")
    if result.timings < 1:
        raise SystemExit("measure_time callback did not record timing")
    if not result.breaker_opened:
        raise SystemExit("circuit breaker did not open")
    print(result)


if __name__ == "__main__":
    main()
