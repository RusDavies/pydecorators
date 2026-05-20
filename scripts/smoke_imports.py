#!/usr/bin/env python
"""Import-smoke check for installed pydecorators package."""

from __future__ import annotations

import pydecorators


def main() -> None:
    missing = [name for name in pydecorators.__all__ if not hasattr(pydecorators, name)]
    if missing:
        joined = ", ".join(sorted(missing))
        raise SystemExit(f"Missing public exports: {joined}")

    for name in pydecorators.__all__:
        getattr(pydecorators, name)

    if not pydecorators.__version__:
        raise SystemExit("pydecorators.__version__ is empty")

    export_count = len(pydecorators.__all__)
    version = pydecorators.__version__
    print(f"Imported pydecorators {version} with {export_count} public exports")


if __name__ == "__main__":
    main()
