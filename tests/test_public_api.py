import pydecorators
from pydecorators.exceptions import (
    ConfigurationError,
    FunctionTimedOut,
    RateLimitExceeded,
    UsefulDecoratorsError,
)


def test_public_exceptions_are_exported() -> None:
    assert pydecorators.UsefulDecoratorsError is UsefulDecoratorsError
    assert pydecorators.ConfigurationError is ConfigurationError
    assert hasattr(pydecorators, "CircuitBreakerOpen")
    assert pydecorators.RateLimitExceeded is RateLimitExceeded
    assert pydecorators.FunctionTimedOut is FunctionTimedOut
    assert hasattr(pydecorators, "EnvRequirementError")


def test_all_exports_existing_attributes() -> None:
    for name in pydecorators.__all__:
        assert hasattr(pydecorators, name)


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

    assert public_decorators <= set(pydecorators.__all__)
