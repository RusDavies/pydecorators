"""Reject moving GitHub Actions refs in workflow ``uses:`` entries.

Third-party actions are executable supply-chain inputs. Pinning to full
40-character commit SHAs keeps trusted-publishing workflows from silently
following a moved tag or branch.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKFLOW_DIR = Path(".github/workflows")
USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _is_external_action(value: str) -> bool:
    """Return whether a uses target should be pinned to an immutable SHA."""

    if value.startswith(("./", ".github/")):
        return False
    # Docker image actions use a separate digest/tag model and are not present in
    # this project today. Keep the error focused on repository actions.
    if value.startswith("docker://"):
        return False
    return "@" in value


def main() -> int:
    failures: list[str] = []

    for path in sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = USES_RE.match(line)
            if not match:
                continue
            target = match.group(1)
            if not _is_external_action(target):
                continue
            _, ref = target.rsplit("@", 1)
            if not FULL_SHA_RE.fullmatch(ref):
                failures.append(f"{path}:{line_number}: {target}")

    if failures:
        print("GitHub Actions uses entries must be pinned to full 40-character commit SHAs:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Workflow action pin policy passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
