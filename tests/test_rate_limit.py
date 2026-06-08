import asyncio
import importlib.util
import math
import multiprocessing
import os
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from pydecorators import ConfigurationError, RateLimitExceeded, rate_limit


class MutableClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeRateLimitRedis:
    def __init__(self) -> None:
        self.zsets: dict[str, list[tuple[float, str]]] = {}
        self.counters: dict[str, int] = {}

    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> list[int]:
        assert "ZREMRANGEBYSCORE" in script
        assert numkeys == 2
        events_key = str(keys_and_args[0])
        sequence_key = str(keys_and_args[1])
        now = float(str(keys_and_args[2]))
        period = float(str(keys_and_args[3]))
        calls = int(str(keys_and_args[4]))
        window = [entry for entry in self.zsets.get(events_key, []) if entry[0] > now - period]
        self.zsets[events_key] = window
        if len(window) < calls:
            sequence = self.counters.get(sequence_key, 0) + 1
            self.counters[sequence_key] = sequence
            window.append((now, f"{now}:{sequence}"))
            window.sort()
            return [0, 0]
        oldest = window[0][0]
        return [1, math.ceil(max(0.0, oldest + period - now) * 1000)]


def _sqlite_rate_limit_worker(
    storage_path: str,
    started: multiprocessing.synchronize.Event,
    results: multiprocessing.Queue[bool],
) -> None:
    @rate_limit(
        calls=3,
        period=60,
        interprocess=True,
        storage_path=storage_path,
        namespace="multiprocessing-stress",
    )
    def limited() -> bool:
        return True

    started.wait(timeout=10)
    try:
        results.put(limited())
    except RateLimitExceeded:
        results.put(False)


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
    with pytest.raises(RateLimitExceeded, match="retry after 10") as exc_info:
        limited()

    assert exc_info.value.retry_after == 10


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

    assert len(successes) == 2
    assert set(successes).issubset({0, 1, 2})
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


def test_rate_limit_cleans_up_idle_keyed_buckets() -> None:
    from pydecorators.rate_limit import _SlidingWindowLimiter

    clock = MutableClock()
    limiter = _SlidingWindowLimiter(calls=1, period=10, clock=clock)

    assert limiter.reserve_or_delay("a") is None
    assert limiter.reserve_or_delay("b") is None
    clock.advance(10)
    assert limiter.reserve_or_delay("c") is None

    assert list(limiter._windows) == ["c"]


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


def test_rate_limit_interprocess_instances_share_storage(tmp_path: Path) -> None:
    clock = MutableClock()
    storage_path = tmp_path / "rate-limit.sqlite3"

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        interprocess=True,
        storage_path=storage_path,
        namespace="shared-api",
    )
    def first() -> str:
        return "first"

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        interprocess=True,
        storage_path=storage_path,
        namespace="shared-api",
    )
    def second() -> str:
        return "second"

    assert first() == "first"
    with pytest.raises(RateLimitExceeded) as exc_info:
        second()

    assert exc_info.value.retry_after == 10


def test_rate_limit_interprocess_namespaces_are_isolated(tmp_path: Path) -> None:
    clock = MutableClock()
    storage_path = tmp_path / "rate-limit.sqlite3"

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        interprocess=True,
        storage_path=storage_path,
        namespace="api-a",
    )
    def api_a() -> str:
        return "a"

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        interprocess=True,
        storage_path=storage_path,
        namespace="api-b",
    )
    def api_b() -> str:
        return "b"

    assert api_a() == "a"
    assert api_b() == "b"
    with pytest.raises(RateLimitExceeded):
        api_a()


def test_rate_limit_interprocess_keyed_buckets_are_isolated(tmp_path: Path) -> None:
    clock = MutableClock()

    @rate_limit(
        calls=1,
        period=10,
        key=lambda tenant: tenant,
        clock=clock,
        interprocess=True,
        storage_path=tmp_path / "rate-limit.sqlite3",
    )
    def limited(tenant: str) -> str:
        return tenant

    assert limited("a") == "a"
    assert limited("b") == "b"
    with pytest.raises(RateLimitExceeded):
        limited("a")


def test_rate_limit_interprocess_sliding_window_resets(tmp_path: Path) -> None:
    clock = MutableClock()

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        interprocess=True,
        storage_path=tmp_path / "rate-limit.sqlite3",
    )
    def limited() -> str:
        return "ok"

    assert limited() == "ok"
    clock.advance(9.9)
    with pytest.raises(RateLimitExceeded):
        limited()
    clock.advance(0.1)
    assert limited() == "ok"


def test_rate_limit_interprocess_block_mode_sleeps_without_reserving_twice(tmp_path: Path) -> None:
    clock = MutableClock()
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    @rate_limit(
        calls=1,
        period=10,
        mode="block",
        clock=clock,
        sleep=fake_sleep,
        interprocess=True,
        storage_path=tmp_path / "rate-limit.sqlite3",
    )
    def limited() -> str:
        return "ok"

    assert limited() == "ok"
    assert limited() == "ok"
    assert sleeps == [10]


def test_rate_limit_interprocess_coordinates_separate_processes(tmp_path: Path) -> None:
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    results: multiprocessing.Queue[bool] = context.Queue()
    processes = [
        context.Process(
            target=_sqlite_rate_limit_worker,
            args=(str(tmp_path / "rate-limit.sqlite3"), started, results),
        )
        for _ in range(12)
    ]

    for process in processes:
        process.start()
    started.set()
    for process in processes:
        process.join(timeout=10)

    try:
        outcomes = [results.get_nowait() for _ in processes]
    except queue.Empty as exc:  # pragma: no cover - indicates a crashed child process
        raise AssertionError("worker process did not report a rate-limit outcome") from exc
    finally:
        for process in processes:
            if process.is_alive():
                process.kill()
                process.join(timeout=5)

    assert all(process.exitcode == 0 for process in processes)
    assert outcomes.count(True) == 3
    assert outcomes.count(False) == 9


def test_rate_limit_distributed_redis_instances_share_storage() -> None:
    clock = MutableClock()
    client = FakeRateLimitRedis()

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        distributed=True,
        redis_client=client,
        redis_key_prefix="demo:v1",
        namespace="shared-api",
    )
    def first() -> str:
        return "first"

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        distributed=True,
        redis_client=client,
        redis_key_prefix="demo:v1",
        namespace="shared-api",
    )
    def second() -> str:
        return "second"

    assert first() == "first"
    with pytest.raises(RateLimitExceeded) as exc_info:
        second()

    assert exc_info.value.retry_after == 10


def test_rate_limit_distributed_redis_namespaces_are_isolated() -> None:
    clock = MutableClock()
    client = FakeRateLimitRedis()

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        distributed=True,
        redis_client=client,
        redis_key_prefix="demo:v1",
        namespace="api-a",
    )
    def api_a() -> str:
        return "a"

    @rate_limit(
        calls=1,
        period=10,
        clock=clock,
        distributed=True,
        redis_client=client,
        redis_key_prefix="demo:v1",
        namespace="api-b",
    )
    def api_b() -> str:
        return "b"

    assert api_a() == "a"
    assert api_b() == "b"
    with pytest.raises(RateLimitExceeded):
        api_a()


def test_rate_limit_distributed_redis_keyed_buckets_are_isolated() -> None:
    clock = MutableClock()

    @rate_limit(
        calls=1,
        period=10,
        key=lambda tenant: tenant,
        clock=clock,
        distributed=True,
        redis_client=FakeRateLimitRedis(),
        redis_key_prefix="demo:v1",
    )
    def limited(tenant: str) -> str:
        return tenant

    assert limited("a") == "a"
    assert limited("b") == "b"
    with pytest.raises(RateLimitExceeded):
        limited("a")


def test_rate_limit_distributed_redis_block_mode_sleeps_without_reserving_twice() -> None:
    clock = MutableClock()
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    @rate_limit(
        calls=1,
        period=10,
        mode="block",
        clock=clock,
        sleep=fake_sleep,
        distributed=True,
        redis_client=FakeRateLimitRedis(),
        redis_key_prefix="demo:v1",
    )
    def limited() -> str:
        return "ok"

    assert limited() == "ok"
    assert limited() == "ok"
    assert sleeps == [10]


def test_rate_limit_distributed_live_redis_integration() -> None:
    redis_url = os.environ.get("PYDECORATORS_REDIS_URL")
    if not redis_url:
        pytest.skip("set PYDECORATORS_REDIS_URL to run live Redis rate-limit integration test")
    redis = pytest.importorskip("redis")
    client = redis.Redis.from_url(redis_url)
    key_prefix = f"pydecorators-test:{uuid.uuid4().hex}"

    @rate_limit(
        calls=2,
        period=60,
        distributed=True,
        redis_client=client,
        redis_key_prefix=key_prefix,
        namespace="live-redis-integration",
    )
    def limited() -> str:
        return "ok"

    try:
        assert limited() == "ok"
        assert limited() == "ok"
        with pytest.raises(RateLimitExceeded) as exc_info:
            limited()
        assert 0 < exc_info.value.retry_after <= 60
        assert list(client.scan_iter(match=f"{key_prefix}:rate_limit:*"))
    finally:
        keys = list(client.scan_iter(match=f"{key_prefix}:rate_limit:*"))
        if keys:
            client.delete(*keys)


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
        ({"calls": 1, "period": 1, "interprocess": True}, "storage_path is required"),
        ({"calls": 1, "period": 1, "storage_path": "x"}, "storage_path is only supported"),
        (
            {"calls": 1, "period": 1, "interprocess": True, "storage_path": "x", "namespace": " "},
            "namespace must not be empty",
        ),
        (
            {
                "calls": 1,
                "period": 1,
                "interprocess": True,
                "storage_path": "x",
                "distributed": True,
            },
            "mutually exclusive",
        ),
        ({"calls": 1, "period": 1, "redis_client": object()}, "Redis options require"),
        ({"calls": 1, "period": 1, "distributed": True}, "redis_client or redis_url"),
        (
            {
                "calls": 1,
                "period": 1,
                "distributed": True,
                "redis_client": object(),
                "redis_key_prefix": "demo",
            },
            "redis_client must provide an eval method",
        ),
        (
            {
                "calls": 1,
                "period": 1,
                "distributed": True,
                "redis_client": FakeRateLimitRedis(),
                "redis_key_prefix": "bad prefix",
            },
            "whitespace",
        ),
        (
            {
                "calls": 1,
                "period": 1,
                "distributed": True,
                "redis_client": FakeRateLimitRedis(),
            },
            "redis_key_prefix is required",
        ),
    ],
)
def test_rate_limit_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        rate_limit(**kwargs)


def test_rate_limit_distributed_url_requires_optional_redis_dependency() -> None:
    if importlib.util.find_spec("redis") is None:
        with pytest.raises(ConfigurationError, match=r"blakemere-wraptools\[redis\]"):
            decorator = rate_limit(
                calls=1,
                period=1,
                distributed=True,
                redis_url="redis://localhost:6379/0",
                redis_key_prefix="demo:v1",
            )

            @decorator
            def limited() -> str:
                return "ok"

            limited()
