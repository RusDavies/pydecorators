import asyncio
import importlib.util
import warnings
from collections.abc import Callable
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


def test_service_shutdown_documentation_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    loaded, closed_signal = examples.service_shutdown_example(tmp_path / "service-cache.sqlite3")

    assert_example_result(loaded, "profile:user-123")
    assert_example_result(closed_signal, "CacheBackendClosedError")


def test_cli_documentation_examples_execute(tmp_path: Path) -> None:
    examples = load_docs_example("cli_examples")

    cache_path = examples.resolve_cache_path("demo-cli", base_path=tmp_path)
    first, second, calls = examples.cached_cli_lookup_example(cache_path)

    assert_example_result(cache_path, tmp_path / "demo-cli" / "cache.sqlite3")
    assert_example_result(first, "user:123")
    assert_example_result(second, "user:123")
    assert_example_result(calls, 1)
    assert_example_result(
        examples.cli_main_style_example(tmp_path / "cli-main.sqlite3", "42"),
        0,
    )
    assert_example_result(
        examples.cli_main_style_example(tmp_path / "cli-main-error.sqlite3", ""),
        2,
    )


def test_json_datetime_bytes_serializer_documentation_example_executes(
    tmp_path: Path,
) -> None:
    from datetime import UTC, datetime

    examples = load_docs_example("disk_cache_backend_examples")
    serializer = examples.DateTimeBytesJsonSerializer()
    expected_created_at = datetime(2026, 5, 11, 12, 30, tzinfo=UTC)
    serialized = serializer.dumps({"created_at": expected_created_at})
    assert_example_result(serializer.loads(serialized)["created_at"], expected_created_at)

    created_at, digest = examples.json_datetime_bytes_serializer_example(
        tmp_path / "json-adapter-cache.sqlite3"
    )

    assert_example_result(created_at, datetime(2026, 5, 11, 12, 30, tzinfo=UTC))
    assert_example_result(digest, b"abc123")


def test_cli_style_inspection_json_documentation_example_executes(
    tmp_path: Path,
) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    output = examples.cli_style_inspection_json_example(tmp_path / "cli-inspect-cache.sqlite3")

    assert_example_result(output["mode"], "aggregate")
    assert_example_result(output["includes_payload_previews"], False)
    assert "sensitivity_warning" in output
    assert "--rows" in output["cli_help"]
    assert "--include-payload-preview" in output["cli_help"]
    assert "entries" not in output


def test_preview_redaction_documentation_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    preview = examples.preview_redaction_example(tmp_path / "redacted-cache.sqlite3")

    assert preview is not None
    assert '"token":"<redacted>"' in preview
    assert "secret" not in preview


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


def _deprecated_assertions(examples: ModuleType) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert_example_result(examples.old_bare_function(1, 2), 3)
        assert_example_result(examples.old_configured_function(1, 2), 3)
        assert_example_result(asyncio.run(examples.old_async_function()), "data")
        assert_example_result(examples.Client().fetch_old(), "old")


def _public_exception_assertions(examples: ModuleType) -> None:
    assert_example_result(examples.configuration_error_example(), "invalid configuration")
    assert_example_result(examples.circuit_breaker_open_example(), "circuit open")
    assert_example_result(examples.cache_key_error_example(), "unhashable key")
    assert_example_result(examples.cache_serialization_error_example(), "serialization failed")
    assert_example_result(examples.validation_error_example(), "validation failed")
    assert_example_result(examples.rate_limit_exceeded_example(), "rate limited")
    assert_example_result(asyncio.run(examples.function_timed_out_example()), "timed out")
    assert_example_result(examples.env_requirement_error_example(), "missing env")


def _rate_limit_assertions(examples: ModuleType) -> None:
    clock = examples.ExampleClock()
    assert_example_result(clock.advance(1), None)
    assert_example_result(clock(), 101.0)

    assert_example_result(examples.raise_mode_example(), "limited")
    assert_example_result(examples.keyed_bucket_example(), ("called:tenant-a", "called:tenant-b"))
    assert_example_result(examples.block_mode_example(), ("called", [60]))


def _timeout_assertions(examples: ModuleType) -> None:
    assert_example_result(asyncio.run(examples.successful_timeout_example()), "finished")
    assert_example_result(asyncio.run(examples.timeout_failure_example()), "timed out")
    assert_example_result(
        asyncio.run(examples.custom_timeout_exception_example()), "vendor call timed out"
    )


def _log_calls_assertions(examples: ModuleType) -> None:
    redacted = examples.redacted_arguments_example()
    assert any("api_key" in message for message in redacted)
    assert any("<redacted>" in message for message in redacted)
    assert all("secret" not in message for message in redacted)

    summarized = examples.summarized_result_example()
    assert any("{'count': 3}" in message for message in summarized)

    async_messages = asyncio.run(examples.async_logging_example())
    assert any("refresh_user started" in message for message in async_messages)
    assert any("refresh_user finished" in message for message in async_messages)


def _measure_time_assertions(examples: ModuleType) -> None:
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


def _validate_types_assertions(examples: ModuleType) -> None:
    assert_example_result(examples.argument_validation_example(), "hello Ada!")
    assert "argument 'value' expected int" in examples.argument_error_example()
    assert_example_result(examples.return_validation_example(), "ready")
    assert_example_result(asyncio.run(examples.async_validation_example()), "user:anonymous")


def _require_env_assertions(examples: ModuleType) -> None:
    assert_example_result(examples.required_variables_example(), "called")
    assert "API_TOKEN" in examples.missing_variable_example()
    assert "failed validation" in examples.validator_example()
    assert_example_result(asyncio.run(examples.async_require_env_example()), "refreshed")


def _circuit_breaker_assertions(examples: ModuleType) -> None:
    assert_example_result(examples.open_circuit_example(), "fallback")
    assert_example_result(examples.half_open_recovery_example(), ["ok", "ok"])
    assert_example_result(asyncio.run(examples.async_circuit_breaker_example()), "async fallback")


def _retry_assertions(examples: ModuleType) -> None:
    assert_example_result(examples.transient_success_example(), ("ok", [0.25], [1, 2]))
    assert_example_result(examples.predicate_example(), "permanent invalid request")
    assert_example_result(asyncio.run(examples.async_retry_example()), ("user", [0.1]))


def _composition_assertions(examples: ModuleType) -> None:
    assert_example_result(examples.measure_whole_operation_example(), ("user", 1, 1.0))

    messages = examples.log_one_logical_call_example()
    assert sum("call_api started" in message for message in messages) == 1
    assert sum("call_api finished" in message for message in messages) == 1

    assert_example_result(
        examples.circuit_outside_retry_example(), "open after one logical failure"
    )
    assert_example_result(
        asyncio.run(examples.timeout_outside_retry_example()),
        "whole operation timed out",
    )


def _retry_idempotency_assertions(examples: ModuleType) -> None:
    gateway = examples.PaymentGateway()
    gateway.failures_remaining = 0
    assert_example_result(
        gateway.charge(amount_cents=100, idempotency_key="direct"), "charge:100:direct"
    )

    assert_example_result(examples.idempotency_key_example(), ("charge:5000:invoice-123", 3))
    assert_example_result(examples.retry_read_example(), "ready")


def _readme_assertions(examples: ModuleType) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert_example_result(examples.old_function(), "still works")
        assert_example_result(examples.deprecated_readme_example(), "still works")
    assert_example_result(examples.call_service(), "ok")
    assert_example_result(examples.retry_readme_example(), "ok")
    assert_example_result(examples.call_user_api("user-123"), "ok:user-123")
    assert_example_result(examples.rate_limit_readme_example(), "ok:user-123")
    assert_example_result(asyncio.run(examples.fetch_user("user-123")), "user-123")
    assert_example_result(asyncio.run(examples.timeout_readme_example()), "user-123")

    log_messages = examples.logging_readme_example()
    assert any("authenticate started" in message for message in log_messages)
    assert any("<redacted>" in message for message in log_messages)
    assert all("secret" not in message for message in log_messages)

    timing_result, timings = examples.timing_readme_example()
    assert timing_result is None
    assert_example_result(timings[0].function, "timing_readme_example.<locals>.rebuild_index")
    assert_example_result(timings[0].duration, 0.5)

    assert_example_result(examples.double(21), 42)
    assert_example_result(examples.validate_types_readme_example(), 42)
    assert_example_result(examples.require_env_readme_example(), "ok")
    assert_example_result(examples.call_vendor_api(), "ok")
    assert_example_result(examples.circuit_breaker_readme_example(), "ok")
    examples.expensive_lookup.cache_clear()
    assert_example_result(examples.expensive_lookup("ada"), "ADA")
    assert_example_result(examples.cache_readme_example(), ("ADA", 1))
    assert_example_result(examples.fetch_user_display_name("user-123"), "User user-123")


def test_readme_disk_cache_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("readme_examples")

    assert_example_result(
        examples.disk_cache_readme_example(tmp_path / "readme-cache.sqlite3"),
        "User user-123",
    )


EXAMPLE_ASSERTIONS: tuple[tuple[str, Callable[[ModuleType], None]], ...] = (
    ("deprecated_examples", _deprecated_assertions),
    ("public_exception_examples", _public_exception_assertions),
    ("rate_limit_examples", _rate_limit_assertions),
    ("timeout_examples", _timeout_assertions),
    ("log_calls_examples", _log_calls_assertions),
    ("measure_time_examples", _measure_time_assertions),
    ("validate_types_examples", _validate_types_assertions),
    ("require_env_examples", _require_env_assertions),
    ("circuit_breaker_examples", _circuit_breaker_assertions),
    ("retry_examples", _retry_assertions),
    ("composition_examples", _composition_assertions),
    ("retry_idempotency_examples", _retry_idempotency_assertions),
    ("readme_examples", _readme_assertions),
)


@pytest.mark.parametrize(("module_name", "assertions"), EXAMPLE_ASSERTIONS)
def test_documentation_examples_execute(
    module_name: str, assertions: Callable[[ModuleType], None]
) -> None:
    assertions(load_docs_example(module_name))
