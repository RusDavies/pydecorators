"""Redis optional-dependency import policy tests."""

from __future__ import annotations

import importlib.util


def test_base_package_import_does_not_require_redis_dependency() -> None:
    """The local cache APIs must import even when Redis is not installed."""

    import useful_decorators

    assert useful_decorators.cache_result is not None
    assert useful_decorators.DiskCacheBackend is not None


def test_redis_backend_is_not_public_until_optional_backend_exists() -> None:
    """Keep the future Redis backend out of public imports until its extra exists."""

    assert importlib.util.find_spec("useful_decorators.redis_backend") is None
