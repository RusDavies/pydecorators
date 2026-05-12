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


def test_rate_limit_documentation_examples_execute() -> None:
    examples = load_docs_example("rate_limit_examples")

    assert_example_result(examples.raise_mode_example(), "limited")
    assert_example_result(examples.keyed_bucket_example(), ("called:tenant-a", "called:tenant-b"))
    assert_example_result(examples.block_mode_example(), ("called", [60]))


def test_timeout_documentation_examples_execute() -> None:
    examples = load_docs_example("timeout_examples")

    assert_example_result(asyncio.run(examples.successful_timeout_example()), "finished")
    assert_example_result(asyncio.run(examples.timeout_failure_example()), "timed out")
    assert_example_result(
        asyncio.run(examples.custom_timeout_exception_example()), "vendor call timed out"
    )


def test_log_calls_documentation_examples_execute() -> None:
    examples = load_docs_example("log_calls_examples")

    redacted = examples.redacted_arguments_example()
    assert any("api_key" in message for message in redacted)
    assert any("<redacted>" in message for message in redacted)
    assert all("secret" not in message for message in redacted)

    summarized = examples.summarized_result_example()
    assert any("{'count': 3}" in message for message in summarized)

    async_messages = asyncio.run(examples.async_logging_example())
    assert any("refresh_user started" in message for message in async_messages)
    assert any("refresh_user finished" in message for message in async_messages)


def test_measure_time_documentation_examples_execute() -> None:
    examples = load_docs_example("measure_time_examples")

    result, info = examples.callback_example()
    assert_example_result(result, "ready")
    assert_example_result(info.function, "callback_example.<locals>.load_report")
    assert_example_result(info.duration, 0.25)
    assert_example_result(info.success, True)

    assert_example_result(
        examples.metrics_hook_example(),
        [("metrics_hook_example.<locals>.rebuild_cache", 0.5, True)],
    )

    async_info = asyncio.run(examples.async_timing_example())
    assert_example_result(async_info.duration, 0.125)
    assert_example_result(async_info.success, True)


def test_validate_types_documentation_examples_execute() -> None:
    examples = load_docs_example("validate_types_examples")

    assert_example_result(examples.argument_validation_example(), "hello Ada!")
    assert "argument 'value' expected int" in examples.argument_error_example()
    assert_example_result(examples.return_validation_example(), "ready")
    assert_example_result(asyncio.run(examples.async_validation_example()), "user:anonymous")


def test_require_env_documentation_examples_execute() -> None:
    examples = load_docs_example("require_env_examples")

    assert_example_result(examples.required_variables_example(), "called")
    assert "API_TOKEN" in examples.missing_variable_example()
    assert "failed validation" in examples.validator_example()
    assert_example_result(asyncio.run(examples.async_require_env_example()), "refreshed")


def test_circuit_breaker_documentation_examples_execute() -> None:
    examples = load_docs_example("circuit_breaker_examples")

    assert_example_result(examples.open_circuit_example(), "fallback")
    assert_example_result(examples.half_open_recovery_example(), ["ok", "ok"])
    assert_example_result(asyncio.run(examples.async_circuit_breaker_example()), "async fallback")


def test_retry_documentation_examples_execute() -> None:
    examples = load_docs_example("retry_examples")

    assert_example_result(examples.transient_success_example(), ("ok", [0.25], [1, 2]))
    assert_example_result(examples.predicate_example(), "permanent invalid request")
    assert_example_result(asyncio.run(examples.async_retry_example()), ("user", [0.1]))
