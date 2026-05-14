import fnmatch
from collections.abc import Callable, Hashable, Iterable
from pathlib import Path
from typing import Protocol

import pytest

from useful_decorators import (
    CacheBackend,
    CacheInfo,
    DiskCacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
)
from useful_decorators.cache_result import _CacheEntry


class MutableClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class BackendFactory(Protocol):
    def __call__(
        self,
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        clock: Callable[[], float] | None = None,
    ) -> CacheBackend: ...


class FakeRedis:
    def __init__(self, *, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or (lambda: 0.0)
        self.values: dict[str, bytes | str | int] = {}
        self.expiries: dict[str, float | None] = {}

    def get(self, name: str) -> bytes | str | int | None:
        expires_at = self.expiries.get(name)
        if expires_at is not None and self._clock() >= expires_at:
            self.delete(name)
            return None
        return self.values.get(name)

    def set(self, name: str, value: bytes | str, *, ex: int | None = None) -> object:
        self.values[name] = value
        self.expiries[name] = self._clock() + ex if ex is not None else None
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
        self.expiries[name] = None
        return value

    def scan_iter(self, match: str) -> Iterable[str | bytes]:
        for key in list(self.values):
            self.get(key)
        return [key for key in self.values if fnmatch.fnmatch(key, match)]


def close_backend(backend: CacheBackend) -> None:
    close = getattr(backend, "close", None)
    if close is not None:
        close()


@pytest.fixture(params=["memory", "disk", "redis"])
def backend_factory(request: pytest.FixtureRequest, tmp_path: Path) -> BackendFactory:
    def make_backend(
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        clock: Callable[[], float] | None = None,
    ) -> CacheBackend:
        if request.param == "memory":
            return MemoryCacheBackend(ttl=ttl, maxsize=maxsize, clock=clock)
        if request.param == "disk":
            return DiskCacheBackend(
                tmp_path / "cache.sqlite3",
                ttl=ttl,
                maxsize=maxsize,
                clock=clock,
            )
        return RedisCacheBackend(
            client=FakeRedis(clock=clock),
            key_prefix=f"conformance:{request.param}",
            ttl=int(ttl) if ttl is not None else None,
            maxsize=maxsize,
        )

    return make_backend


def require_entry(backend: CacheBackend, key: Hashable) -> _CacheEntry:
    entry = backend.get(key)
    assert entry is not None
    return entry


def test_cache_backend_conformance_tracks_hits_misses_and_size(
    backend_factory: BackendFactory,
) -> None:
    backend = backend_factory(maxsize=2)
    try:
        assert backend.get("missing") is None
        backend.set_value("key", "value")

        entry = require_entry(backend, "key")

        assert entry.payload == "value"
        assert entry.is_exception is False
        assert backend.info() == CacheInfo(hits=1, misses=1, maxsize=2, currsize=1)
    finally:
        close_backend(backend)


def test_cache_backend_conformance_clear_resets_entries_and_stats(
    backend_factory: BackendFactory,
) -> None:
    backend = backend_factory()
    try:
        assert backend.get("missing") is None
        backend.set_value("key", "value")
        assert backend.get("key") is not None

        backend.clear()

        assert backend.get("key") is None
        assert backend.info() == CacheInfo(hits=0, misses=1, maxsize=128, currsize=0)
    finally:
        close_backend(backend)


def test_cache_backend_conformance_stores_cached_exceptions(
    backend_factory: BackendFactory,
) -> None:
    backend = backend_factory()
    try:
        backend.set_exception("key", ValueError("boom"))

        entry = require_entry(backend, "key")

        assert isinstance(entry.payload, ValueError)
        assert str(entry.payload) == "boom"
        assert entry.is_exception is True
        assert backend.info().hits == 1
    finally:
        close_backend(backend)


def test_cache_backend_conformance_expires_entries(backend_factory: BackendFactory) -> None:
    clock = MutableClock()
    backend = backend_factory(ttl=10, clock=clock)
    try:
        backend.set_value("key", "value")
        clock.advance(11)

        assert backend.get("key") is None
        assert backend.info() == CacheInfo(hits=0, misses=1, maxsize=128, currsize=0)
    finally:
        close_backend(backend)


def test_cache_backend_conformance_evicts_least_recently_used_entry(
    backend_factory: BackendFactory,
) -> None:
    clock = MutableClock()
    backend = backend_factory(maxsize=2, clock=clock)
    try:
        backend.set_value("a", "A")
        clock.advance(1)
        backend.set_value("b", "B")
        clock.advance(1)
        assert backend.get("a") is not None
        clock.advance(1)
        backend.set_value("c", "C")

        assert backend.get("b") is None
        assert require_entry(backend, "a").payload == "A"
        assert require_entry(backend, "c").payload == "C"
        assert backend.info().currsize == 2
    finally:
        close_backend(backend)


def test_cache_backend_conformance_replaces_existing_entries(
    backend_factory: BackendFactory,
) -> None:
    backend = backend_factory()
    try:
        backend.set_value("key", "old")
        backend.set_value("key", "new")

        assert require_entry(backend, "key").payload == "new"
        assert backend.info().currsize == 1
    finally:
        close_backend(backend)
