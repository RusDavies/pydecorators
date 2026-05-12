import useful_decorators
from useful_decorators.exceptions import (
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UsefulDecoratorsError,
)


def test_public_exceptions_are_exported() -> None:
    assert useful_decorators.UsefulDecoratorsError is UsefulDecoratorsError
    assert useful_decorators.ConfigurationError is ConfigurationError
    assert hasattr(useful_decorators, "CircuitBreakerOpen")
    assert useful_decorators.RateLimitExceeded is RateLimitExceeded
    assert useful_decorators.FunctionTimedOut is FunctionTimedOut
    assert hasattr(useful_decorators, "EnvRequirementError")


def test_all_exports_existing_attributes() -> None:
    for name in useful_decorators.__all__:
        assert hasattr(useful_decorators, name)


def test_public_decorators_are_exported_via_all() -> None:
    public_decorators = {
        "cache_result",
        "circuit_breaker",
        "deprecated",
        "log_calls",
        "measure_time",
        "rate_limit",
        "require_env",
        "retry",
        "timeout",
        "validate_types",
    }

    assert public_decorators <= set(useful_decorators.__all__)
