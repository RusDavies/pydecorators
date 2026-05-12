import asyncio
import importlib.util
import warnings
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.docs_policy


def load_docs_example(module_name: str) -> ModuleType:
    example_path = Path("docs/examples") / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, example_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_example_result(actual: object, expected: object) -> None:
    assert actual == expected


def test_deprecated_documentation_examples_execute() -> None:
    examples = load_docs_example("deprecated_examples")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert_example_result(examples.old_bare_function(1, 2), 3)
        assert_example_result(examples.old_configured_function(1, 2), 3)
        assert_example_result(asyncio.run(examples.old_async_function()), "data")
        assert_example_result(examples.Client().fetch_old(), "old")


def test_disk_cache_backend_documentation_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    assert_example_result(examples.fetch_user_display_name("user-123"), "User user-123")
    first, second, calls = examples.disk_cache_example(tmp_path / "cache.sqlite3")

    assert_example_result(first, "User user-123")
    assert_example_result(second, "User user-123")
    assert_example_result(calls, 1)


def test_disk_cache_backend_persistence_documentation_example_executes(
    tmp_path: Path,
) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    first, second, calls = examples.persistent_disk_cache_example(
        tmp_path / "persistent-cache.sqlite3"
    )

    assert_example_result(first, "User user-456")
    assert_example_result(second, "User user-456")
    assert_example_result(calls, 1)


def test_disk_cache_backend_context_manager_documentation_example_executes(
    tmp_path: Path,
) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    value, hits = examples.scoped_disk_cache_example(tmp_path / "scoped-cache.sqlite3")

    assert_example_result(value, "cached")
    assert_example_result(hits, 1)


def test_cache_backend_closed_error_documentation_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    assert_example_result(
        examples.closed_backend_error_example(tmp_path / "closed-cache.sqlite3"), "closed"
    )


def test_json_datetime_bytes_serializer_documentation_example_executes(
    tmp_path: Path,
) -> None:
    from datetime import UTC, datetime

    examples = load_docs_example("disk_cache_backend_examples")

    created_at, digest = examples.json_datetime_bytes_serializer_example(
        tmp_path / "json-adapter-cache.sqlite3"
    )

    assert_example_result(created_at, datetime(2026, 5, 11, 12, 30, tzinfo=UTC))
    assert_example_result(digest, b"abc123")


def test_json_cache_row_inspection_documentation_example_executes(
    tmp_path: Path,
) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    payload, content_type, filename = examples.inspect_json_cache_row_example(
        tmp_path / "inspect-json-cache.sqlite3"
    )

    assert_example_result(payload, '{"id":"user-123","active":true}')
    assert_example_result(content_type, "application/json")
    assert_example_result(filename, "inspect-json-cache.sqlite3")


def test_public_exception_documentation_examples_execute() -> None:
    examples = load_docs_example("public_exception_examples")

    assert_example_result(examples.configuration_error_example(), "invalid configuration")
    assert_example_result(examples.circuit_breaker_open_example(), "circuit open")
    assert_example_result(examples.cache_key_error_example(), "unhashable key")
    assert_example_result(examples.cache_serialization_error_example(), "serialization failed")
    assert_example_result(examples.rate_limit_exceeded_example(), "rate limited")
    assert_example_result(asyncio.run(examples.function_timed_out_example()), "timed out")
    assert_example_result(examples.env_requirement_error_example(), "missing env")
