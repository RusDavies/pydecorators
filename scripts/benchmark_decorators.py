"""Small optional benchmark suite for decorator overhead.

This is not part of default CI. It is a quick local sanity tool for comparing rough
per-call overhead when changing wrapper internals.
"""

from __future__ import annotations

import argparse
import logging
import statistics
import time
from collections.abc import Callable

from useful_decorators import cache_result, log_calls, measure_time, retry, validate_types


def _plain(value: int) -> int:
    return value + 1


@cache_result(maxsize=128)
def _cached(value: int) -> int:
    return value + 1


@retry(attempts=1, delay=0)
def _retried(value: int) -> int:
    return value + 1


@measure_time()
def _measured(value: int) -> int:
    return value + 1


_LOGGER = logging.getLogger("useful_decorators.benchmark")
_LOGGER.addHandler(logging.NullHandler())
_LOGGER.propagate = False


@log_calls(logger=_LOGGER)
def _logged(value: int) -> int:
    return value + 1


@validate_types()
def _validated(value: int) -> int:
    return value + 1


def benchmark(function: Callable[[int], int], *, iterations: int) -> float:
    """Return average seconds per call for a simple unary function."""

    started = time.perf_counter()
    for index in range(iterations):
        function(index % 64)
    elapsed = time.perf_counter() - started
    return elapsed / iterations


def run(iterations: int, rounds: int) -> dict[str, float]:
    """Run benchmark rounds and return median seconds per call by scenario."""

    scenarios: dict[str, Callable[[int], int]] = {
        "plain": _plain,
        "cache_result_hot": _cached,
        "retry_attempts_1": _retried,
        "measure_time_noop": _measured,
        "log_calls_noop": _logged,
        "validate_types_shallow": _validated,
    }
    results: dict[str, float] = {}
    for name, function in scenarios.items():
        samples = [benchmark(function, iterations=iterations) for _ in range(rounds)]
        results[name] = statistics.median(samples)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark useful-decorators overhead.")
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()

    for name, seconds_per_call in run(args.iterations, args.rounds).items():
        print(f"{name}: {seconds_per_call * 1_000_000:.2f} us/call")


if __name__ == "__main__":
    main()
