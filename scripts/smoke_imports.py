#!/usr/bin/env python
"""Import-smoke check for installed useful_decorators package."""

from __future__ import annotations

import useful_decorators


def main() -> None:
    missing = [name for name in useful_decorators.__all__ if not hasattr(useful_decorators, name)]
    if missing:
        joined = ", ".join(sorted(missing))
        raise SystemExit(f"Missing public exports: {joined}")

    for name in useful_decorators.__all__:
        getattr(useful_decorators, name)

    if not useful_decorators.__version__:
        raise SystemExit("useful_decorators.__version__ is empty")

    export_count = len(useful_decorators.__all__)
    version = useful_decorators.__version__
    print(f"Imported useful_decorators {version} with {export_count} public exports")


if __name__ == "__main__":
    main()
