"""Useful decorators for everyday Python projects.

The package is intentionally small and boring: reliability, caching, rate limiting,
timeouts, and developer ergonomics without dragging in a framework-shaped sofa.
"""

from useful_decorators.cache_result import (
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
    cache_namespace,
    cache_result,
    redact_json_preview,
)
from useful_decorators.circuit_breaker import CircuitBreakerOpen, CircuitState, circuit_breaker
from useful_decorators.deprecated import deprecated
from useful_decorators.exceptions import (
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
from useful_decorators.log_calls import log_calls
from useful_decorators.measure_time import TimingInfo, measure_time
from useful_decorators.rate_limit import rate_limit
from useful_decorators.require_env import EnvRequirementError, require_env
from useful_decorators.retry import retry
from useful_decorators.timeout import timeout
from useful_decorators.validate_types import validate_types

__version__ = "0.1.0"

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
    "TimingInfo",
    "UnsupportedCacheSchemaVersionError",
    "UsefulDecoratorsError",
    "ValidationError",
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
