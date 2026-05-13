#!/usr/bin/env python3
"""Print a tiny Markdown coverage summary from coverage.xml."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def coverage_percent(path: Path) -> float:
    root = ET.parse(path).getroot()
    return float(root.attrib["line-rate"]) * 100


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coverage_xml", type=Path, nargs="?", default=Path("coverage.xml"))
    args = parser.parse_args()

    percent = coverage_percent(args.coverage_xml)
    print("## Coverage")
    print(f"Line coverage: {percent:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
