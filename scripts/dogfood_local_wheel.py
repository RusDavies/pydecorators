#!/usr/bin/env python
"""Run dogfood scripts against the locally built wheel in a clean venv."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
DOGFOOD_DIR = PROJECT_ROOT / "dogfood"


def run(command: list[str], *, cwd: Path = PROJECT_ROOT, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def latest_wheel() -> Path:
    wheels = sorted(
        DIST_DIR.glob("blakemere_decorators-*.whl"),
        key=lambda path: path.stat().st_mtime,
    )
    if not wheels:
        raise SystemExit("No blakemere_decorators wheel found in dist/")
    return wheels[-1]


def main() -> None:
    run([sys.executable, "-m", "build", "--wheel"])
    wheel = latest_wheel()

    with tempfile.TemporaryDirectory(prefix="blakemere-decorators-dogfood-") as tmp:
        venv_dir = Path(tmp) / "venv"
        run([sys.executable, "-m", "venv", str(venv_dir)])
        python = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        env = {**os.environ, "PYTHONPATH": "", "DOGFOOD_API_TOKEN": "dogfood-secret"}
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"], env=env)
        run([str(python), "-m", "pip", "install", str(wheel)], env=env)
        for scenario in sorted(DOGFOOD_DIR.glob("*.py")):
            if scenario.name.startswith("_"):
                continue
            run([str(python), str(scenario)], cwd=Path(tmp), env=env)

    print(f"Dogfood wheel scenarios passed for {wheel.name}")


if __name__ == "__main__":
    main()
