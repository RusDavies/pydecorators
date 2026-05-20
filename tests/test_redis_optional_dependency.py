"""Redis optional-dependency import policy tests."""

from __future__ import annotations


def test_base_package_import_does_not_require_redis_dependency() -> None:
    """The public package imports even when Redis is not installed."""

    import pydecorators

    assert pydecorators.cache_result is not None
    assert pydecorators.DiskCacheBackend is not None
    assert pydecorators.RedisCacheBackend is not None


def test_redis_backend_module_import_does_not_import_redis_dependency() -> None:
    """Importing the backend module should not require redis-py until URL construction."""

    from pydecorators.redis_backend import RedisCacheBackend

    assert RedisCacheBackend is not None
