"""In-memory result caching decorator."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from threading import RLock
from typing import Any, Protocol, cast, runtime_checkable

from useful_decorators._core import is_async_callable, mirror_metadata, monotonic
from useful_decorators._typing import Clock, P, R
from useful_decorators.exceptions import CacheKeyError, ConfigurationError

_KW_MARKER = object()
_TYPE_MARKER = object()


@dataclass(frozen=True, slots=True)
class CacheInfo:
    """Cache statistics exposed by ``cache_info()`` on cached functions."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int


@dataclass(slots=True)
class _CacheEntry:
    """Internal cache entry for values or cached exceptions."""

    payload: Any
    expires_at: float | None
    is_exception: bool = False


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol implemented by cache storage backends."""

    def get(self, key: Hashable) -> _CacheEntry | None:
        """Return a cached entry for *key*, or ``None`` for a miss."""

    def set_value(self, key: Hashable, value: object) -> None:
        """Store a successful cached value."""

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        """Store an exception payload for later re-raising."""

    def clear(self) -> None:
        """Clear cached entries and reset statistics where supported."""

    def info(self) -> CacheInfo:
        """Return cache statistics."""


class MemoryCacheBackend:
    """Thread-safe in-memory cache backend used by ``@cache_result``.

    This backend owns storage, TTL pruning, LRU eviction, and hit/miss
    statistics. The decorator remains responsible for key generation and for
    executing wrapped functions outside backend locks.
    """

    def __init__(
        self,
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        clock: Clock | None = None,
    ) -> None:
        if ttl is not None and ttl <= 0:
            raise ConfigurationError("ttl must be greater than zero when provided")
        if maxsize is not None and maxsize <= 0:
            raise ConfigurationError("maxsize must be greater than zero when provided")

        self._ttl = ttl
        self._maxsize = maxsize
        self._clock = clock or monotonic
        self._lock = RLock()
        self._cache: OrderedDict[Hashable, _CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: Hashable) -> _CacheEntry | None:
        """Return a cache entry for *key*, or ``None`` after recording a miss."""

        with self._lock:
            entry = self._cache.get(key)
            if entry is not None:
                if self._is_expired(entry):
                    self._cache.pop(key, None)
                else:
                    self._hits += 1
                    self._cache.move_to_end(key)
                    return entry
            self._misses += 1
            return None

    def set_value(self, key: Hashable, value: object) -> None:
        """Store a successful cached value."""

        self._set_entry(key, _CacheEntry(value, expires_at=self._expires_at()))

    def set_exception(self, key: Hashable, exception: BaseException) -> None:
        """Store an exception payload for later re-raising."""

        self._set_entry(
            key,
            _CacheEntry(exception, expires_at=self._expires_at(), is_exception=True),
        )

    def clear(self) -> None:
        """Clear cached entries and reset statistics."""

        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def info(self) -> CacheInfo:
        """Return current cache statistics after pruning expired entries."""

        with self._lock:
            self._prune_expired()
            return CacheInfo(
                hits=self._hits,
                misses=self._misses,
                maxsize=self._maxsize,
                currsize=len(self._cache),
            )

    def _set_entry(self, key: Hashable, entry: _CacheEntry) -> None:
        with self._lock:
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._evict_if_needed()

    def _is_expired(self, entry: _CacheEntry) -> bool:
        return entry.expires_at is not None and self._clock() >= entry.expires_at

    def _expires_at(self) -> float | None:
        if self._ttl is None:
            return None
        return self._clock() + self._ttl

    def _evict_if_needed(self) -> None:
        if self._maxsize is None:
            return
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def _prune_expired(self) -> None:
        expired_keys = [key for key, entry in self._cache.items() if self._is_expired(entry)]
        for expired_key in expired_keys:
            self._cache.pop(expired_key, None)


def _ensure_hashable(value: object) -> Hashable:
    try:
        hash(value)
    except TypeError as exc:
        raise CacheKeyError("cache key must be hashable") from exc
    return value


def _default_cache_key(
    args: tuple[object, ...], kwargs: dict[str, object], *, typed: bool
) -> Hashable:
    key_parts: tuple[object, ...] = args
    if kwargs:
        key_parts += (_KW_MARKER,)
        key_parts += tuple(sorted(kwargs.items()))
    if typed:
        key_parts += (_TYPE_MARKER,)
        key_parts += tuple(type(arg) for arg in args)
        if kwargs:
            key_parts += tuple((name, type(value)) for name, value in sorted(kwargs.items()))
    return _ensure_hashable(key_parts)


def cache_result(
    *,
    ttl: float | None = None,
    maxsize: int | None = 128,
    key: Callable[..., Hashable] | None = None,
    typed: bool = False,
    cache_exceptions: bool = False,
    clock: Clock | None = None,
    backend: CacheBackend | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Cache results from a synchronous function using a configurable backend.

    Async callables are intentionally rejected for ``v0.1.0`` until async cache
    semantics are designed separately.
    """

    cache_backend = backend or MemoryCacheBackend(ttl=ttl, maxsize=maxsize, clock=clock)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if is_async_callable(func):
            raise ConfigurationError("cache_result does not support async functions yet")

        def make_key(args: tuple[object, ...], kwargs: dict[str, object]) -> Hashable:
            if key is not None:
                return _ensure_hashable(key(*args, **kwargs))
            return _default_cache_key(args, kwargs, typed=typed)

        def cache_info() -> CacheInfo:
            return cache_backend.info()

        def cache_clear() -> None:
            cache_backend.clear()

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache_key = make_key(cast(tuple[object, ...], args), cast(dict[str, object], kwargs))
            entry = cache_backend.get(cache_key)
            if entry is not None:
                if entry.is_exception:
                    raise cast(BaseException, entry.payload)
                return cast(R, entry.payload)

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                if cache_exceptions:
                    cache_backend.set_exception(cache_key, exc)
                raise

            cache_backend.set_value(cache_key, result)
            return result

        wrapped = mirror_metadata(wrapper, func)
        wrapped_with_cache_api = cast(Any, wrapped)
        wrapped_with_cache_api.cache_info = cache_info
        wrapped_with_cache_api.cache_clear = cache_clear
        return wrapped

    return decorator
