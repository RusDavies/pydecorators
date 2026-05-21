"""Useful decorators for everyday Python projects.

The package is intentionally small and boring: reliability, caching, rate limiting,
timeouts, and developer ergonomics without dragging in a framework-shaped sofa.
"""

from pydecorators.cache_result import (
    CacheBackend,
    CacheCoalescingInfo,
    CacheInfo,
    CacheSerializer,
    DiskCacheAggregateInspectionReport,
    DiskCacheBackend,
    DiskCacheDropEvent,
    DiskCacheInspectionEntry,
    DiskCacheInspectionReport,
    DiskCacheIntegrityReport,
    DiskCacheMaintenanceReport,
    DiskCacheMetadata,
    DiskCachePreviewContext,
    JsonCacheSerializer,
    MemoryCacheBackend,
    PickleCacheSerializer,
    cache_directory,
    cache_namespace,
    cache_result,
    redact_json_preview,
)
from pydecorators.circuit_breaker import CircuitBreakerOpen, CircuitState, circuit_breaker
from pydecorators.deprecated import deprecated
from pydecorators.exceptions import (
    CacheBackendClosedError,
    CacheKeyError,
    CacheSerializationError,
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UnsupportedCacheSchemaVersionError,
    UsefulDecoratorsError,
    ValidationError,
)
from pydecorators.log_calls import log_calls
from pydecorators.measure_time import TimingInfo, measure_time
from pydecorators.rate_limit import rate_limit
from pydecorators.redis_backend import RedisCacheBackend, RedisCacheClient
from pydecorators.require_env import EnvRequirementError, require_env
from pydecorators.retry import retry
from pydecorators.timeout import timeout
from pydecorators.validate_types import validate_types

__version__ = "0.1.4"

__all__ = [
    "CacheBackend",
    "CacheBackendClosedError",
    "CacheCoalescingInfo",
    "CacheInfo",
    "CacheKeyError",
    "CacheSerializationError",
    "CacheSerializer",
    "CircuitBreakerOpen",
    "CircuitState",
    "ConfigurationError",
    "DiskCacheAggregateInspectionReport",
    "DiskCacheBackend",
    "DiskCacheDropEvent",
    "DiskCacheInspectionEntry",
    "DiskCacheInspectionReport",
    "DiskCacheIntegrityReport",
    "DiskCacheMaintenanceReport",
    "DiskCacheMetadata",
    "DiskCachePreviewContext",
    "EnvRequirementError",
    "FunctionTimedOut",
    "JsonCacheSerializer",
    "MemoryCacheBackend",
    "PickleCacheSerializer",
    "RateLimitExceeded",
    "RedisCacheBackend",
    "RedisCacheClient",
    "TimingInfo",
    "UnsupportedCacheSchemaVersionError",
    "UsefulDecoratorsError",
    "ValidationError",
    "cache_directory",
    "cache_namespace",
    "cache_result",
    "circuit_breaker",
    "deprecated",
    "log_calls",
    "measure_time",
    "rate_limit",
    "redact_json_preview",
    "require_env",
    "retry",
    "timeout",
    "validate_types",
]
