"""In-memory result caching decorator."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from threading import RLock
from typing import Any, cast

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
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Cache results from a synchronous function in process memory.

    Async callables are intentionally rejected for ``v0.1.0`` until async cache
    semantics are designed separately.
    """

    if ttl is not None and ttl <= 0:
        raise ConfigurationError("ttl must be greater than zero when provided")
    if maxsize is not None and maxsize <= 0:
        raise ConfigurationError("maxsize must be greater than zero when provided")

    _ = clock or monotonic

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if is_async_callable(func):
            raise ConfigurationError("cache_result does not support async functions yet")

        lock = RLock()
        cache: OrderedDict[Hashable, _CacheEntry] = OrderedDict()
        hits = 0
        misses = 0

        def make_key(args: tuple[object, ...], kwargs: dict[str, object]) -> Hashable:
            if key is not None:
                return _ensure_hashable(key(*args, **kwargs))
            return _default_cache_key(args, kwargs, typed=typed)

        def cache_info() -> CacheInfo:
            with lock:
                return CacheInfo(hits=hits, misses=misses, maxsize=maxsize, currsize=len(cache))

        def cache_clear() -> None:
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = 0
                misses = 0

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal hits, misses
            cache_key = make_key(cast(tuple[object, ...], args), cast(dict[str, object], kwargs))
            with lock:
                entry = cache.get(cache_key)
                if entry is not None:
                    hits += 1
                    cache.move_to_end(cache_key)
                    if entry.is_exception:
                        raise cast(BaseException, entry.payload)
                    return cast(R, entry.payload)
                misses += 1

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                if cache_exceptions:
                    with lock:
                        cache[cache_key] = _CacheEntry(exc, expires_at=None, is_exception=True)
                raise

            with lock:
                cache[cache_key] = _CacheEntry(result, expires_at=None)
            return result

        wrapped = mirror_metadata(wrapper, func)
        wrapped_with_cache_api = cast(Any, wrapped)
        wrapped_with_cache_api.cache_info = cache_info
        wrapped_with_cache_api.cache_clear = cache_clear
        return wrapped

    return decorator
