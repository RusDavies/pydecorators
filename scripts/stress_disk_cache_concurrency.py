"""Optional long-running DiskCacheBackend concurrency stress test.

This script is intentionally outside default CI. Use it when investigating SQLite locking
or local filesystem behavior under heavier thread contention.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from pydecorators import DiskCacheBackend


def run_stress(cache_path: Path, *, workers: int, operations: int) -> tuple[int, int, int]:
    """Run a write/read stress loop and return hits, misses, and current size."""

    backend = DiskCacheBackend(cache_path, maxsize=workers * 4, busy_timeout_ms=10_000)

    def write_then_read(index: int) -> None:
        key = f"key-{index % (workers * 2)}"
        backend.set_value(key, {"index": index})
        entry = backend.get(key)
        assert entry is not None
        assert isinstance(entry.payload, dict)

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            list(executor.map(write_then_read, range(operations)))
        info = backend.info()
        return info.hits, info.misses, info.currsize
    finally:
        backend.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress DiskCacheBackend concurrency.")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--operations", type=int, default=5_000)
    parser.add_argument("--path", type=Path)
    args = parser.parse_args()

    if args.path is not None:
        hits, misses, currsize = run_stress(
            args.path,
            workers=args.workers,
            operations=args.operations,
        )
    else:
        with TemporaryDirectory() as directory:
            hits, misses, currsize = run_stress(
                Path(directory) / "stress.sqlite3",
                workers=args.workers,
                operations=args.operations,
            )

    print(f"hits={hits} misses={misses} currsize={currsize}")


if __name__ == "__main__":
    main()
