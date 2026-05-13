"""Executable examples for public exception documentation."""

import asyncio
from contextlib import suppress

from useful_decorators import (
    CacheKeyError,
    CacheSerializationError,
    CircuitBreakerOpen,
    ConfigurationError,
    EnvRequirementError,
    FunctionTimedOut,
    PickleCacheSerializer,
    RateLimitExceeded,
    ValidationError,
    cache_result,
    circuit_breaker,
    rate_limit,
    require_env,
    timeout,
)


def configuration_error_example() -> str:
    """Handle invalid decorator configuration."""

    try:
        cache_result(namespace="   ")
    except ConfigurationError:
        return "invalid configuration"
    return "valid"


def circuit_breaker_open_example() -> str:
    """Handle an open circuit breaker."""

    @circuit_breaker(failure_threshold=1, reset_timeout=10)
    def call_service() -> None:
        raise RuntimeError("down")

    with suppress(RuntimeError):
        call_service()

    try:
        call_service()
    except CircuitBreakerOpen:
        return "circuit open"
    return "circuit closed"


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


def validation_error_example() -> str:
    """Handle a runtime type-validation failure."""

    from useful_decorators import validate_types

    @validate_types()
    def double(value: int) -> int:
        return value * 2

    try:
        double("bad")  # type: ignore[arg-type]
    except ValidationError:
        return "validation failed"
    return "validation passed"


def rate_limit_exceeded_example() -> str:
    """Handle a rate-limited call."""

    @rate_limit(calls=1, period=60)
    def limited() -> str:
        return "ok"

    limited()
    try:
        limited()
    except RateLimitExceeded:
        return "rate limited"
    return "allowed"


async def function_timed_out_example() -> str:
    """Handle an async timeout."""

    @timeout(seconds=0.01)
    async def slow() -> str:
        await asyncio.sleep(1)
        return "late"

    try:
        await slow()
    except FunctionTimedOut:
        return "timed out"
    return "finished"


def env_requirement_error_example() -> str:
    """Handle a missing required environment variable."""

    @require_env("API_TOKEN", environ={})
    def call_service() -> str:
        return "called"

    try:
        call_service()
    except EnvRequirementError:
        return "missing env"
    return "env present"
