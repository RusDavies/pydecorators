"""Executable Django/FastAPI-style examples without requiring those frameworks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydecorators import (
    DiskCacheBackend,
    cache_directory,
    cache_namespace,
    cache_result,
    retry,
)


@dataclass(frozen=True)
class Response:
    """Tiny response stand-in used by the executable examples."""

    status_code: int
    body: dict[str, Any]


class FakeRequest:
    """Tiny request stand-in with the attributes these examples need."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id


def django_view_cache_example(cache_path: Path) -> tuple[Response, Response, int]:
    """Cache a Django-style view helper while keeping the view itself simple."""

    calls = 0
    backend = DiskCacheBackend(cache_path, ttl=60, maxsize=32)

    @cache_result(backend=backend, namespace=cache_namespace("django-profile", 1))
    def load_profile(user_id: str) -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"id": user_id, "name": f"User {user_id}"}

    def profile_view(request: FakeRequest) -> Response:
        return Response(status_code=200, body=load_profile(request.user_id))

    try:
        first = profile_view(FakeRequest("123"))
        second = profile_view(FakeRequest("123"))
        return first, second, calls
    finally:
        backend.close()


def fastapi_dependency_cache_example(
    cache_path: Path,
) -> tuple[dict[str, str], dict[str, str], int]:
    """Cache a FastAPI-style dependency/helper rather than the route wrapper."""

    calls = 0
    backend = DiskCacheBackend(cache_path, ttl=60, maxsize=32)

    @cache_result(backend=backend, namespace=cache_namespace("fastapi-settings", 1))
    def load_tenant_settings(tenant_id: str) -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"tenant_id": tenant_id, "plan": "starter"}

    def read_settings(tenant_id: str) -> dict[str, str]:
        return load_tenant_settings(tenant_id)

    try:
        first = read_settings("acme")
        second = read_settings("acme")
        return first, second, calls
    finally:
        backend.close()


def service_cache_path_example(base_path: Path) -> Path:
    """Resolve a framework service cache path under the conventional cache root."""

    return cache_directory("example-web-service", base_path=base_path) / "cache.sqlite3"


def retrying_service_client_example() -> tuple[str, int]:
    """Retry a framework service-client helper outside the request wrapper."""

    attempts = 0

    @retry(attempts=2, delay=0, exceptions=(ConnectionError,))
    def call_inventory_service(sku: str) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("transient inventory timeout")
        return f"available:{sku}"

    return call_inventory_service("sku-123"), attempts
