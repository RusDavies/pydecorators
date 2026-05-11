from typing import Any, cast

import pytest

from useful_decorators import CacheInfo, cache_result
from useful_decorators.exceptions import CacheKeyError, ConfigurationError


def get_cache_info(func: object) -> CacheInfo:
    return cast(CacheInfo, cast(Any, func).cache_info())


def clear_cache(func: object) -> None:
    cast(Any, func).cache_clear()


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
