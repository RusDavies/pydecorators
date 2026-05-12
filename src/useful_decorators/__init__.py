"""Useful decorators for everyday Python projects.

The package is intentionally small and boring: reliability, caching, rate limiting,
timeouts, and developer ergonomics without dragging in a framework-shaped sofa.
"""

from useful_decorators.cache_result import (
    CacheBackend,
    CacheInfo,
    CacheSerializer,
    DiskCacheBackend,
    DiskCacheDropEvent,
    JsonCacheSerializer,
    MemoryCacheBackend,
    PickleCacheSerializer,
    cache_result,
)
from useful_decorators.deprecated import deprecated
from useful_decorators.exceptions import (
    CacheBackendClosedError,
    CacheKeyError,
    CacheSerializationError,
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UsefulDecoratorsError,
)
from useful_decorators.log_calls import log_calls
from useful_decorators.measure_time import TimingInfo, measure_time
from useful_decorators.rate_limit import rate_limit
from useful_decorators.retry import retry
from useful_decorators.timeout import timeout

__version__ = "0.1.0"

__all__ = [
    "CacheBackend",
    "CacheBackendClosedError",
    "CacheInfo",
    "CacheKeyError",
    "CacheSerializationError",
    "CacheSerializer",
    "ConfigurationError",
    "DiskCacheBackend",
    "DiskCacheDropEvent",
    "FunctionTimedOut",
    "JsonCacheSerializer",
    "MemoryCacheBackend",
    "PickleCacheSerializer",
    "RateLimitExceeded",
    "TimingInfo",
    "UsefulDecoratorsError",
    "cache_result",
    "deprecated",
    "log_calls",
    "measure_time",
    "rate_limit",
    "retry",
    "timeout",
]
