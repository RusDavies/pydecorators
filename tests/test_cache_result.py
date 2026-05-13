from collections.abc import Hashable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event, Lock
from time import sleep
from typing import Any, cast

import pytest

from useful_decorators import (
    CacheBackendClosedError,
    CacheCoalescingInfo,
    CacheInfo,
    DiskCacheBackend,
    MemoryCacheBackend,
    cache_namespace,
    cache_result,
)
from useful_decorators.cache_result import _CacheEntry
from useful_decorators.exceptions import CacheKeyError, ConfigurationError


def get_cache_info(func: object) -> CacheInfo:
    return cast(CacheInfo, cast(Any, func).cache_info())


def clear_cache(func: object) -> None:
    cast(Any, func).cache_clear()


def get_coalescing_info(func: object) -> CacheCoalescingInfo:
    return cast(CacheCoalescingInfo, cast(Any, func).cache_coalescing_info())


def test_cache_result_caches_sync_hits_and_misses() -> None:
    calls = 0

    @cache_result()
    def add(left: int, right: int) -> int:
        nonlocal calls
        calls += 1
        return left + right

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert calls == 1
    assert get_cache_info(add) == CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)


def test_cache_result_distinguishes_kwargs_order() -> None:
    calls = 0

    @cache_result()
    def join(*, first: str, second: str) -> str:
        nonlocal calls
        calls += 1
        return first + second

    assert join(first="a", second="b") == "ab"
    assert join(second="b", first="a") == "ab"
    assert calls == 1


def test_cache_result_supports_custom_key_function() -> None:
    calls = 0

    @cache_result(key=lambda value: value.lower())
    def normalize(value: str) -> str:
        nonlocal calls
        calls += 1
        return value.upper()

    assert normalize("Hello") == "HELLO"
    assert normalize("hello") == "HELLO"
    assert calls == 1


def test_cache_result_typed_key_distinguishes_value_types() -> None:
    calls = 0

    @cache_result(typed=True)
    def identify(value: object) -> str:
        nonlocal calls
        calls += 1
        return type(value).__name__

    assert identify(1) == "int"
    assert identify(1.0) == "float"
    assert calls == 2


def test_cache_result_rejects_unhashable_default_key() -> None:
    @cache_result()
    def count_values(values: list[int]) -> int:
        return len(values)

    with pytest.raises(CacheKeyError, match="cache key must be hashable"):
        count_values([1, 2, 3])


def test_cache_result_rejects_unhashable_custom_key() -> None:
    @cache_result(key=lambda value: [value])  # type: ignore[arg-type, return-value]
    def identity(value: int) -> int:
        return value

    with pytest.raises(CacheKeyError, match="cache key must be hashable"):
        identity(1)


def test_cache_result_preserves_metadata() -> None:
    @cache_result()
    def add(left: int, right: int) -> int:
        """Add two values."""

        return left + right

    assert add.__name__ == "add"
    assert add.__doc__ == "Add two values."
    assert add.__annotations__ == {"left": int, "right": int, "return": int}
    assert cast(Any, add).__wrapped__ is not None


async def async_function() -> int:
    return 1


def test_cache_result_rejects_async_functions() -> None:
    with pytest.raises(ConfigurationError, match="does not support async functions yet"):
        cache_result()(async_function)


def test_cache_clear_resets_cache_and_statistics() -> None:
    calls = 0

    @cache_result()
    def value() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert value() == 1
    assert value() == 1
    assert get_cache_info(value).hits == 1

    clear_cache(value)

    assert get_cache_info(value) == CacheInfo(hits=0, misses=0, maxsize=128, currsize=0)
    assert value() == 2


def test_cache_result_rejects_invalid_configuration() -> None:
    with pytest.raises(ConfigurationError, match="ttl must be greater than zero"):
        cache_result(ttl=0)
    with pytest.raises(ConfigurationError, match="maxsize must be greater than zero"):
        cache_result(maxsize=0)


def test_cache_result_caches_exceptions_when_enabled() -> None:
    calls = 0

    @cache_result(cache_exceptions=True)
    def fail_once(value: int) -> int:
        nonlocal calls
        calls += 1
        raise RuntimeError(f"boom {value}")

    with pytest.raises(RuntimeError, match="boom 1"):
        fail_once(1)
    with pytest.raises(RuntimeError, match="boom 1"):
        fail_once(1)

    assert calls == 1
    assert get_cache_info(fail_once) == CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)


def test_cache_result_does_not_cache_exceptions_by_default() -> None:
    calls = 0

    @cache_result()
    def fail(value: int) -> int:
        nonlocal calls
        calls += 1
        raise RuntimeError(f"boom {value}")

    with pytest.raises(RuntimeError, match="boom 1"):
        fail(1)
    with pytest.raises(RuntimeError, match="boom 1"):
        fail(1)

    assert calls == 2
    assert get_cache_info(fail) == CacheInfo(hits=0, misses=2, maxsize=128, currsize=0)


def test_cache_result_executes_wrapped_function_outside_cache_lock() -> None:
    import threading

    entered_first = threading.Event()
    release_first = threading.Event()
    entered_second = threading.Event()

    @cache_result()
    def wait_for_release(value: int) -> int:
        if value == 1:
            entered_first.set()
            assert release_first.wait(timeout=2)
        if value == 2:
            entered_second.set()
        return value

    first_thread = threading.Thread(target=lambda: wait_for_release(1))
    first_thread.start()
    assert entered_first.wait(timeout=2)

    second_thread = threading.Thread(target=lambda: wait_for_release(2))
    second_thread.start()
    assert entered_second.wait(timeout=2)

    release_first.set()
    first_thread.join(timeout=2)
    second_thread.join(timeout=2)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()


def test_cache_result_default_keys_do_not_canonicalize_call_styles() -> None:
    calls = 0

    @cache_result()
    def add(left: int, right: int = 0) -> int:
        nonlocal calls
        calls += 1
        return left + right

    assert add(1, right=2) == 3
    assert add(left=1, right=2) == 3

    assert calls == 2
    assert get_cache_info(add) == CacheInfo(hits=0, misses=2, maxsize=128, currsize=2)


def test_cache_result_typed_key_distinguishes_keyword_value_types() -> None:
    calls = 0

    @cache_result(typed=True)
    def identify(*, value: object) -> str:
        nonlocal calls
        calls += 1
        return type(value).__name__

    assert identify(value=1) == "int"
    assert identify(value=1.0) == "float"
    assert calls == 2


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_cache_result_expires_entries_after_ttl() -> None:
    clock = FakeClock()
    calls = 0

    @cache_result(ttl=10, clock=clock)
    def value() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert value() == 1
    assert value() == 1
    clock.advance(10)
    assert value() == 2
    assert get_cache_info(value) == CacheInfo(hits=1, misses=2, maxsize=128, currsize=1)


def test_cache_result_can_refresh_ttl_on_hit() -> None:
    clock = FakeClock()
    calls = 0

    @cache_result(ttl=10, refresh_ttl_on_hit=True, clock=clock)
    def value() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert value() == 1
    clock.advance(9)
    assert value() == 1
    clock.advance(9)
    assert value() == 1
    clock.advance(10)
    assert value() == 2
    assert get_cache_info(value) == CacheInfo(hits=2, misses=2, maxsize=128, currsize=1)


def test_cache_result_does_not_refresh_ttl_on_hit_by_default() -> None:
    clock = FakeClock()
    calls = 0

    @cache_result(ttl=10, clock=clock)
    def value() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert value() == 1
    clock.advance(9)
    assert value() == 1
    clock.advance(1)
    assert value() == 2


def test_cache_info_prunes_expired_entries() -> None:
    clock = FakeClock()

    @cache_result(ttl=5, clock=clock)
    def value(number: int) -> int:
        return number

    assert value(1) == 1
    clock.advance(5)

    assert get_cache_info(value) == CacheInfo(hits=0, misses=1, maxsize=128, currsize=0)


def test_cache_result_evicts_least_recently_used_entry_when_maxsize_is_exceeded() -> None:
    calls = 0

    @cache_result(maxsize=2)
    def value(number: int) -> int:
        nonlocal calls
        calls += 1
        return number

    assert value(1) == 1
    assert value(2) == 2
    assert value(1) == 1
    assert value(3) == 3
    assert value(2) == 2

    assert calls == 4
    assert get_cache_info(value) == CacheInfo(hits=1, misses=4, maxsize=2, currsize=2)


def test_cache_result_supports_unbounded_maxsize() -> None:
    calls = 0

    @cache_result(maxsize=None)
    def value(number: int) -> int:
        nonlocal calls
        calls += 1
        return number

    for number in range(10):
        assert value(number) == number

    assert calls == 10
    assert get_cache_info(value).currsize == 10
    assert get_cache_info(value).maxsize is None


def test_cache_result_sync_cache_mutation_is_thread_safe() -> None:
    import threading

    @cache_result(maxsize=32)
    def value(number: int) -> int:
        return number

    errors: list[BaseException] = []

    def worker(offset: int) -> None:
        try:
            for index in range(200):
                assert value((index + offset) % 40) >= 0
        except BaseException as exc:  # pragma: no cover - only fails on race bugs
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(offset,)) for offset in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not errors
    assert all(not thread.is_alive() for thread in threads)
    assert get_cache_info(value).currsize <= 32


def test_cache_result_cached_exceptions_expire_after_ttl() -> None:
    clock = FakeClock()
    calls = 0

    @cache_result(ttl=10, cache_exceptions=True, clock=clock)
    def fail() -> int:
        nonlocal calls
        calls += 1
        raise RuntimeError(f"boom {calls}")

    with pytest.raises(RuntimeError, match="boom 1"):
        fail()
    with pytest.raises(RuntimeError, match="boom 1"):
        fail()

    clock.advance(10)

    with pytest.raises(RuntimeError, match="boom 2"):
        fail()

    assert calls == 2
    assert get_cache_info(fail) == CacheInfo(hits=1, misses=2, maxsize=128, currsize=1)


class RecordingBackend:
    def __init__(self) -> None:
        self.entries: dict[object, object] = {}
        self.hits = 0
        self.misses = 0
        self.cleared = False

    def get(self, key: Hashable) -> _CacheEntry | None:
        if key in self.entries:
            self.hits += 1
            return _CacheEntry(self.entries[key], expires_at=None)
        self.misses += 1
        return None

    def set_value(self, key: Hashable, value: object) -> None:
        self.entries[key] = value

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        self.entries[key] = exception

    def clear(self) -> None:
        self.entries.clear()
        self.cleared = True

    def info(self) -> CacheInfo:
        return CacheInfo(
            hits=self.hits, misses=self.misses, maxsize=None, currsize=len(self.entries)
        )


def test_cache_result_accepts_custom_backend() -> None:
    backend = RecordingBackend()
    calls = 0

    @cache_result(backend=backend)
    def value(number: int) -> int:
        nonlocal calls
        calls += 1
        return number * 2

    assert value(2) == 4
    assert value(2) == 4
    assert calls == 1
    assert get_cache_info(value) == CacheInfo(hits=1, misses=1, maxsize=None, currsize=1)

    clear_cache(value)
    assert backend.cleared


def test_cache_result_rejects_closed_backend_at_configuration_time(tmp_path: Path) -> None:
    backend = DiskCacheBackend(tmp_path / "cache.sqlite3")
    backend.close()

    with pytest.raises(CacheBackendClosedError, match="cache backend is closed"):
        cache_result(backend=backend)


def test_shared_backend_shares_entries_for_identical_generated_keys() -> None:
    backend = MemoryCacheBackend()
    first_calls = 0
    second_calls = 0

    @cache_result(backend=backend)
    def first(value: int) -> str:
        nonlocal first_calls
        first_calls += 1
        return f"first:{value}"

    @cache_result(backend=backend)
    def second(value: int) -> str:
        nonlocal second_calls
        second_calls += 1
        return f"second:{value}"

    assert first(1) == "first:1"
    assert second(1) == "first:1"
    assert first_calls == 1
    assert second_calls == 0


def test_namespace_isolates_shared_backend_entries() -> None:
    backend = MemoryCacheBackend()
    first_calls = 0
    second_calls = 0

    @cache_result(backend=backend, namespace="first")
    def first(value: int) -> str:
        nonlocal first_calls
        first_calls += 1
        return f"first:{value}"

    @cache_result(backend=backend, namespace="second")
    def second(value: int) -> str:
        nonlocal second_calls
        second_calls += 1
        return f"second:{value}"

    assert first(1) == "first:1"
    assert second(1) == "second:1"
    assert first(1) == "first:1"
    assert second(1) == "second:1"
    assert first_calls == 1
    assert second_calls == 1


def test_cache_namespace_builds_versioned_namespace() -> None:
    assert cache_namespace("users", 1) == "users:v1"
    assert cache_namespace(" users ", "v2") == "users:v2"


@pytest.mark.parametrize(
    ("name", "version", "message"),
    [
        (" ", 1, "cache namespace name must not be empty"),
        ("users:admin", 1, "cache namespace name must not contain ':'"),
        ("users", 0, "cache namespace version must be positive"),
        ("users", " ", "cache namespace version must not be empty"),
        ("users", "v1:beta", "cache namespace version must not contain ':'"),
    ],
)
def test_cache_namespace_rejects_ambiguous_parts(
    name: str,
    version: int | str,
    message: str,
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        cache_namespace(name, version)


def test_cache_result_rejects_empty_namespace() -> None:
    with pytest.raises(ConfigurationError, match="namespace must not be empty"):
        cache_result(namespace=" ")


def test_custom_key_function_controls_namespace_separation() -> None:
    backend = MemoryCacheBackend()
    calls = 0

    @cache_result(backend=backend, namespace="ignored", key=lambda value: value)
    def value(number: int) -> str:
        nonlocal calls
        calls += 1
        return f"value:{number}"

    assert value(1) == "value:1"
    assert value(1) == "value:1"
    assert calls == 1


def test_cache_result_exposes_empty_coalescing_diagnostics() -> None:
    @cache_result(coalesce_misses=True)
    def value(number: int) -> int:
        return number

    info = get_coalescing_info(value)

    assert info == CacheCoalescingInfo(
        current_in_flight=0,
        total_waiters=0,
        total_wait_seconds=0.0,
    )


def test_cache_result_can_coalesce_duplicate_concurrent_misses() -> None:
    calls = 0
    started = Event()
    release = Event()

    @cache_result(coalesce_misses=True)
    def slow_value(key: str) -> str:
        nonlocal calls
        calls += 1
        started.set()
        assert release.wait(timeout=5)
        return f"value:{key}"

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(slow_value, "same")
        assert started.wait(timeout=5)
        second = executor.submit(slow_value, "same")
        sleep(0.05)
        assert calls == 1
        release.set()

        assert first.result(timeout=5) == "value:same"
        assert second.result(timeout=5) == "value:same"

    assert calls == 1
    info = get_coalescing_info(slow_value)
    assert info.current_in_flight == 0
    assert info.total_waiters == 1
    assert info.total_wait_seconds > 0


def test_cache_result_coalescing_stress_many_waiters_on_one_key() -> None:
    calls = 0
    started = Event()
    release = Event()

    @cache_result(coalesce_misses=True)
    def slow_value(key: str) -> str:
        nonlocal calls
        calls += 1
        started.set()
        assert release.wait(timeout=5)
        return f"value:{key}"

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(slow_value, "same") for _ in range(12)]
        assert started.wait(timeout=5)
        sleep(0.05)
        assert calls == 1
        release.set()

        assert [future.result(timeout=5) for future in futures] == ["value:same"] * 12

    info = get_coalescing_info(slow_value)
    assert calls == 1
    assert info.current_in_flight == 0
    assert info.total_waiters == 11
    assert info.total_wait_seconds > 0


def test_cache_result_coalescing_does_not_block_different_keys() -> None:
    barrier = Barrier(2)
    calls: list[int] = []
    calls_lock = Lock()

    @cache_result(coalesce_misses=True)
    def slow_value(key: int) -> int:
        with calls_lock:
            calls.append(key)
        barrier.wait(timeout=5)
        return key * 10

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(slow_value, 1)
        second = executor.submit(slow_value, 2)

        assert first.result(timeout=5) == 10
        assert second.result(timeout=5) == 20

    assert sorted(calls) == [1, 2]


def test_cache_result_coalescing_does_not_broadcast_uncached_exceptions() -> None:
    calls = 0
    started = Event()
    release = Event()

    @cache_result(coalesce_misses=True)
    def fails(key: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            assert release.wait(timeout=5)
        raise ValueError(f"boom {calls}: {key}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(fails, "same")
        assert started.wait(timeout=5)
        second = executor.submit(fails, "same")
        sleep(0.05)
        release.set()

        with pytest.raises(ValueError, match="boom 1: same"):
            first.result(timeout=5)
        with pytest.raises(ValueError, match="boom 2: same"):
            second.result(timeout=5)

    assert calls == 2


def test_cache_result_coalescing_reuses_cached_exceptions_when_enabled() -> None:
    calls = 0
    started = Event()
    release = Event()

    @cache_result(coalesce_misses=True, cache_exceptions=True)
    def fails(key: str) -> str:
        nonlocal calls
        calls += 1
        started.set()
        assert release.wait(timeout=5)
        raise ValueError(f"boom: {key}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(fails, "same")
        assert started.wait(timeout=5)
        second = executor.submit(fails, "same")
        sleep(0.05)
        release.set()

        with pytest.raises(ValueError, match="boom: same"):
            first.result(timeout=5)
        with pytest.raises(ValueError, match="boom: same"):
            second.result(timeout=5)

    assert calls == 1
