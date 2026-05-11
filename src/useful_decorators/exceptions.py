"""Public exception hierarchy for useful-decorators."""


class UsefulDecoratorsError(Exception):
    """Base class for all package-specific exceptions."""


class ConfigurationError(ValueError, UsefulDecoratorsError):
    """Raised when a decorator receives invalid configuration."""


class RateLimitExceeded(UsefulDecoratorsError):
    """Raised when a rate-limited call exceeds its configured allowance."""


class FunctionTimedOut(TimeoutError, UsefulDecoratorsError):
    """Raised when a decorated function exceeds its configured timeout."""


class CacheKeyError(TypeError, UsefulDecoratorsError):
    """Raised when ``@cache_result`` cannot build a hashable cache key."""


class CacheSerializationError(UsefulDecoratorsError):
    """Raised when cache serialization or deserialization fails."""


class CacheBackendClosedError(UsefulDecoratorsError):
    """Raised when a cache backend is used after it has been closed."""
