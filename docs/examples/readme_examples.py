"""Executable README snippets.

These examples mirror the compact README usage blocks while keeping side effects local so
copy-paste examples cannot quietly drift into decorative fiction.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from useful_decorators import (
    CircuitBreakerOpen,
    DiskCacheBackend,
    TimingInfo,
    cache_namespace,
    cache_result,
    circuit_breaker,
    deprecated,
    log_calls,
    measure_time,
    rate_limit,
    require_env,
    retry,
    timeout,
    validate_types,
)


@deprecated("Kept for compatibility.", replacement="new_function", version="0.1.0")
def old_function() -> str:
    """README deprecation example."""

    return "still works"


def deprecated_readme_example() -> str:
    """Run the README deprecation snippet."""

    return old_function()


@retry(attempts=3, delay=0.25, backoff=2, exceptions=ConnectionError, sleep=lambda _: None)
def call_service() -> str:
    """README retry example."""

    return "ok"


def retry_readme_example() -> str:
    """Run the README retry snippet."""

    return call_service()


@rate_limit(calls=10, period=60, key=lambda user_id: user_id)
def call_user_api(user_id: str) -> str:
    """README rate-limit example."""

    return f"ok:{user_id}"


def rate_limit_readme_example() -> str:
    """Run the README rate-limit snippet."""

    return call_user_api("user-123")


@timeout(seconds=2)
async def fetch_user(user_id: str) -> str:
    """README timeout example."""

    await asyncio.sleep(0)
    return user_id


async def timeout_readme_example() -> str:
    """Run the README timeout snippet."""

    return await fetch_user("user-123")


def logging_readme_example() -> list[str]:
    """Run the README logging snippet with a local in-memory handler."""

    messages: list[str] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    logger = logging.getLogger("useful_decorators.readme_examples.logging")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(ListHandler())

    @log_calls(logger=logger, include_args=True, redact_args={"password"})
    def authenticate(*, username: str, password: str) -> bool:
        return bool(username and password)

    authenticate(username="ada", password="secret")
    return messages


def timing_readme_example() -> tuple[None, list[TimingInfo]]:
    """Run the README timing snippet."""

    timings: list[TimingInfo] = []

    @measure_time(callback=timings.append, clock=iter([10.0, 10.5]).__next__)
    def rebuild_index() -> None:
        pass

    return rebuild_index(), timings


@validate_types(validate_return=True)
def double(value: int) -> int:
    """README type-validation example."""

    return value * 2


def validate_types_readme_example() -> int:
    """Run the README type-validation snippet."""

    return double(21)


def require_env_readme_example() -> str:
    """Run the README environment-requirement snippet."""

    @require_env("API_TOKEN", environ={"API_TOKEN": "present"})
    def call_configured_service() -> str:
        return "ok"

    return call_configured_service()


@circuit_breaker(failure_threshold=2, reset_timeout=10)
def call_vendor_api() -> str:
    """README circuit-breaker example."""

    return "ok"


def circuit_breaker_readme_example() -> str:
    """Run the README circuit-breaker snippet."""

    try:
        return call_vendor_api()
    except CircuitBreakerOpen:
        return "fallback"


@cache_result(maxsize=128)
def expensive_lookup(value: str) -> str:
    """README memory-cache example."""

    return value.upper()


def cache_readme_example() -> tuple[str, int]:
    """Run the README memory-cache snippet."""

    expensive_lookup.cache_clear()  # type: ignore[attr-defined]
    expensive_lookup("ada")
    second = expensive_lookup("ada")
    return second, expensive_lookup.cache_info().hits  # type: ignore[attr-defined]


def fetch_user_display_name(user_id: str) -> str:
    """Small local replacement for the README's application-specific fetch helper."""

    return f"User {user_id}"


def disk_cache_readme_example(path: Path) -> str:
    """Run the README disk-cache lifecycle snippet."""

    backend = DiskCacheBackend(path, ttl=3600, maxsize=10_000)

    @cache_result(backend=backend, namespace=cache_namespace("users", 1))
    def load_user_display_name(user_id: str) -> str:
        return fetch_user_display_name(user_id)

    try:
        return load_user_display_name("user-123")
    finally:
        backend.close()
