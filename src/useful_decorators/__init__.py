"""Useful decorators for everyday Python projects.

The package is intentionally small and boring: reliability, caching, rate limiting,
timeouts, and developer ergonomics without dragging in a framework-shaped sofa.
"""

from useful_decorators.cache_result import CacheInfo
from useful_decorators.deprecated import deprecated
from useful_decorators.exceptions import (
    CacheKeyError,
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UsefulDecoratorsError,
)

__version__ = "0.1.0"

__all__ = [
    "CacheInfo",
    "CacheKeyError",
    "ConfigurationError",
    "FunctionTimedOut",
    "RateLimitExceeded",
    "UsefulDecoratorsError",
    "deprecated",
]
