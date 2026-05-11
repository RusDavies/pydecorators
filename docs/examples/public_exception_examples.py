"""Executable examples for public exception documentation."""

from useful_decorators import (
    CacheKeyError,
    CacheSerializationError,
    ConfigurationError,
    PickleCacheSerializer,
    cache_result,
)


def configuration_error_example() -> str:
    """Handle invalid decorator configuration."""

    try:
        cache_result(namespace="   ")
    except ConfigurationError:
        return "invalid configuration"
    return "valid"


def cache_key_error_example() -> str:
    """Handle an unhashable cache key produced at call time."""

    @cache_result()
    def identity(value: list[int]) -> list[int]:
        return value

    try:
        identity([1, 2, 3])
    except CacheKeyError:
        return "unhashable key"
    return "hashable key"


def cache_serialization_error_example() -> str:
    """Handle serializer failures from unsupported payloads."""

    serializer = PickleCacheSerializer()

    try:
        serializer.dumps(lambda value: value)
    except CacheSerializationError:
        return "serialization failed"
    return "serialization succeeded"
