"""Tests for optional Redis cache backend."""

from __future__ import annotations

import fnmatch
import importlib.util
from collections.abc import Iterable

import pytest

from useful_decorators import (
    CacheSerializationError,
    ConfigurationError,
    RedisCacheBackend,
    cache_result,
)
from useful_decorators.redis_backend import RedisCacheClient


class FakeRedis:
    """Small in-memory Redis stand-in for backend contract tests."""

    def __init__(self) -> None:
        self.values: dict[str, bytes | str | int] = {}
        self.expiries: dict[str, int | None] = {}

    def get(self, name: str) -> bytes | str | int | None:
        return self.values.get(name)

    def set(self, name: str, value: bytes | str, *, ex: int | None = None) -> object:
        self.values[name] = value
        self.expiries[name] = ex
        return True

    def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            if name in self.values:
                deleted += 1
            self.values.pop(name, None)
            self.expiries.pop(name, None)
        return deleted

    def incr(self, name: str) -> int:
        value = int(self.values.get(name, 0)) + 1
        self.values[name] = value
        return value

    def scan_iter(self, match: str) -> Iterable[str | bytes]:
        return [key for key in self.values if fnmatch.fnmatch(key, match)]


def test_redis_backend_implements_cache_backend_contract() -> None:
    client = FakeRedis()
    backend = RedisCacheBackend(client=client, key_prefix="demo:v1", ttl=60)
    calls = 0

    @cache_result(backend=backend, namespace="users")
    def load_user(user_id: str) -> str:
        nonlocal calls
        calls += 1
        return f"user:{user_id}"

    assert load_user("123") == "user:123"
    assert load_user("123") == "user:123"
    assert calls == 1
    assert backend.info().hits == 1
    assert backend.info().misses == 1
    assert backend.info().currsize == 1
    assert set(client.expiries.values()) >= {60}


def test_redis_backend_caches_exceptions() -> None:
    backend = RedisCacheBackend(client=FakeRedis(), key_prefix="exceptions:v1")
    calls = 0

    @cache_result(backend=backend, cache_exceptions=True)
    def flaky() -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        flaky()
    with pytest.raises(RuntimeError, match="boom"):
        flaky()
    assert calls == 1
    assert backend.info().hits == 1


def test_redis_backend_clear_removes_entries_and_stats() -> None:
    backend = RedisCacheBackend(client=FakeRedis(), key_prefix="clear:v1")

    backend.set_value("answer", 42)
    assert backend.get("answer") is not None
    backend.clear()

    assert backend.get("answer") is None
    assert backend.info().hits == 0
    assert backend.info().misses == 1
    assert backend.info().currsize == 0


def test_redis_backend_drops_corrupt_entries_as_misses() -> None:
    client = FakeRedis()
    backend = RedisCacheBackend(client=client, key_prefix="corrupt:v1")
    backend.set_value("answer", 42)
    entry_key = next(key for key in client.values if ":entry:" in key)
    client.values[entry_key] = b"not-json"

    assert backend.get("answer") is None
    assert entry_key not in client.values
    assert backend.info().misses == 1


def test_redis_backend_validates_configuration() -> None:
    with pytest.raises(ConfigurationError, match="key_prefix"):
        RedisCacheBackend(client=FakeRedis(), key_prefix="  ")
    with pytest.raises(ConfigurationError, match="whitespace"):
        RedisCacheBackend(client=FakeRedis(), key_prefix="bad prefix")
    with pytest.raises(ConfigurationError, match="ttl"):
        RedisCacheBackend(client=FakeRedis(), key_prefix="demo", ttl=0)
    with pytest.raises(ConfigurationError, match="either Redis client or url"):
        RedisCacheBackend(client=FakeRedis(), url="redis://localhost", key_prefix="demo")


def test_redis_backend_requires_optional_dependency_for_url() -> None:
    if importlib.util.find_spec("redis") is None:
        with pytest.raises(ConfigurationError, match=r"blakemere-decorators\[redis\]"):
            RedisCacheBackend(url="redis://localhost", key_prefix="demo")


def test_fake_redis_satisfies_client_protocol() -> None:
    assert isinstance(FakeRedis(), RedisCacheClient)


def test_redis_backend_surfaces_unserializable_keys() -> None:
    backend = RedisCacheBackend(client=FakeRedis(), key_prefix="keys:v1")

    with pytest.raises(CacheSerializationError, match="cache key"):
        backend.set_value(lambda: None, "value")
