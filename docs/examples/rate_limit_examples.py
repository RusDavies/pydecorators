"""Executable examples for @rate_limit documentation."""

from pydecorators import RateLimitExceeded, rate_limit


class ExampleClock:
    """Small controllable clock for deterministic rate-limit examples."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def raise_mode_example() -> str:
    """Reject calls after the local sliding-window budget is exhausted."""

    clock = ExampleClock()

    @rate_limit(calls=1, period=60, clock=clock)
    def call_api() -> str:
        return "called"

    call_api()
    try:
        call_api()
    except RateLimitExceeded:
        return "limited"
    return "allowed"


def keyed_bucket_example() -> tuple[str, str]:
    """Use a key function to isolate independent rate-limit buckets."""

    clock = ExampleClock()

    @rate_limit(calls=1, period=60, key=lambda tenant_id: tenant_id, clock=clock)
    def call_tenant_api(tenant_id: str) -> str:
        return f"called:{tenant_id}"

    first = call_tenant_api("tenant-a")
    second = call_tenant_api("tenant-b")
    return first, second


def block_mode_example() -> tuple[str, list[float]]:
    """Inject sleep and clock functions so block-mode examples do not really wait."""

    clock = ExampleClock()
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    @rate_limit(calls=1, period=60, mode="block", clock=clock, sleep=fake_sleep)
    def call_api() -> str:
        return "called"

    call_api()
    result = call_api()
    return result, sleeps
