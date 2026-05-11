"""Useful decorators for everyday Python projects.

The package is intentionally small and boring: reliability, caching, rate limiting,
timeouts, and developer ergonomics without dragging in a framework-shaped sofa.
"""

from useful_decorators.cache_result import (
    CacheBackend,
    CacheInfo,
    CacheSerializer,
    MemoryCacheBackend,
    PickleCacheSerializer,
    cache_result,
)
from useful_decorators.deprecated import deprecated
from useful_decorators.exceptions import (
    CacheKeyError,
    CacheSerializationError,
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UsefulDecoratorsError,
)

__version__ = "0.1.0"

__all__ = [
    "CacheBackend",
    "CacheInfo",
    "CacheKeyError",
    "CacheSerializationError",
    "CacheSerializer",
    "ConfigurationError",
    "FunctionTimedOut",
    "MemoryCacheBackend",
    "PickleCacheSerializer",
    "RateLimitExceeded",
    "UsefulDecoratorsError",
    "cache_result",
    "deprecated",
]
