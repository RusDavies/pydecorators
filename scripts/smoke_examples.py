#!/usr/bin/env python
"""Smoke-load executable documentation examples."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "docs" / "examples"


def load_example(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load example module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    example_files = sorted(path for path in EXAMPLES_DIR.glob("*_examples.py"))
    if not example_files:
        raise SystemExit(f"No executable example files found in {EXAMPLES_DIR}")

    for path in example_files:
        load_example(path)

    print(f"Loaded {len(example_files)} executable documentation example modules")


if __name__ == "__main__":
    main()
