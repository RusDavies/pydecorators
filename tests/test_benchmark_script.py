"""Smoke tests for optional benchmark tooling."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_benchmark_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "benchmark_decorators", "scripts/benchmark_decorators.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_benchmark_script_runs_small_sample() -> None:
    benchmark = load_benchmark_module()

    results = benchmark.run(iterations=16, rounds=1)

    assert set(results) == {
        "plain",
        "cache_result_hot",
        "retry_attempts_1",
        "measure_time_noop",
        "log_calls_noop",
        "validate_types_shallow",
    }
    assert all(value >= 0 for value in results.values())


def test_benchmark_script_documents_optional_ci_posture() -> None:
    text = Path("scripts/benchmark_decorators.py").read_text()

    assert "not part of default CI" in text
    assert "per-call overhead" in text
