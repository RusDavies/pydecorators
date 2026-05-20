#!/usr/bin/env python3
"""Check whether a Python package name currently exists on PyPI/TestPyPI."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_NAME = "pydecorators"
REPOSITORIES = {
    "pypi": "https://pypi.org/pypi/{name}/json",
    "testpypi": "https://test.pypi.org/pypi/{name}/json",
}


@dataclass(frozen=True)
class PackageStatus:
    repository: str
    url: str
    exists: bool
    detail: str


def check_repository(repository: str, package_name: str, timeout: float) -> PackageStatus:
    url = REPOSITORIES[repository].format(name=package_name)
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            return PackageStatus(repository, url, exists=False, detail="404 Not Found")
        return PackageStatus(repository, url, exists=True, detail=f"HTTP {exc.code}")
    except URLError as exc:
        raise SystemExit(f"{repository}: failed to check {url}: {exc.reason}") from exc

    version = payload.get("info", {}).get("version", "unknown")
    return PackageStatus(repository, url, exists=True, detail=f"published version {version}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=PROJECT_NAME, help="package name to check")
    parser.add_argument(
        "--repository",
        choices=sorted(REPOSITORIES),
        action="append",
        help="repository to check; defaults to PyPI and TestPyPI",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repositories = args.repository or sorted(REPOSITORIES)
    statuses = [check_repository(repo, args.name, args.timeout) for repo in repositories]

    for status in statuses:
        state = "exists" if status.exists else "available"
        print(f"{status.repository}: {args.name}: {state} ({status.detail})")

    return 1 if any(status.exists for status in statuses) else 0


if __name__ == "__main__":
    raise SystemExit(main())
