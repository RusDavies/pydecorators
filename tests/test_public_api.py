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
    assert useful_decorators.RateLimitExceeded is RateLimitExceeded
    assert useful_decorators.FunctionTimedOut is FunctionTimedOut


def test_all_exports_existing_attributes() -> None:
    for name in useful_decorators.__all__:
        assert hasattr(useful_decorators, name)
