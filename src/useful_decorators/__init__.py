"""Useful decorators for everyday Python projects.

The package is intentionally small and boring: reliability, caching, rate limiting,
timeouts, and developer ergonomics without dragging in a framework-shaped sofa.
"""

from useful_decorators.exceptions import (
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UsefulDecoratorsError,
)

__version__ = "0.1.0"

__all__ = [
    "ConfigurationError",
    "FunctionTimedOut",
    "RateLimitExceeded",
    "UsefulDecoratorsError",
]
