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
