#!/usr/bin/env python
"""Dogfood installed wheel against a real local project script without modifying it."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
TARGET_SCRIPT_ENV = "PYDECORATORS_EXTERNAL_DOGFOOD_SCRIPT"

RUNNER = r"""
from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

from pydecorators import log_calls, measure_time, retry, validate_types

script = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("gateway_sim_dogfood", script)
if spec is None or spec.loader is None:
    raise SystemExit(f"could not load {script}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

logger = logging.getLogger("dogfood.external_gateway")
timings = []

route_request = measure_time(callback=timings.append)(
    log_calls(logger=logger)(
        retry(attempts=2, delay=0)(
            validate_types()(module.route_request)
        )
    )
)

policy = module.load_policy()
requests = [
    module.Request("dogfood-1", "support-answering-default", "internal", "ca", 1200),
    module.Request("dogfood-2", "regulated-data-no-retention", "regulated", "us", 1200),
    module.Request(
        "dogfood-3",
        "support-answering-default",
        "internal",
        "ca",
        1200,
        provider_health="down",
    ),
]
events = [route_request(request, policy=policy) for request in requests]

if events[0]["policy_decision"] != "allow":
    raise SystemExit(f"expected allow, got {events[0]}")
if events[1]["policy_decision"] != "deny":
    raise SystemExit(f"expected deny, got {events[1]}")
if events[2]["fallback_used"] is not True:
    raise SystemExit(f"expected fallback, got {events[2]}")
if len(timings) != len(events):
    raise SystemExit(f"expected {len(events)} timings, got {len(timings)}")

print(f"external dogfood passed: {len(events)} routed requests, {len(timings)} timings")
"""


def run(command: list[str], *, cwd: Path = PROJECT_ROOT, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def latest_wheel() -> Path:
    wheels = sorted(
        DIST_DIR.glob("blakemere_wraptools-*.whl"),
        key=lambda path: path.stat().st_mtime,
    )
    if not wheels:
        raise SystemExit("No blakemere-wraptools wheel found in dist/")
    return wheels[-1]


def target_script() -> Path | None:
    configured = os.environ.get(TARGET_SCRIPT_ENV)
    if not configured:
        return None
    return Path(configured).expanduser().resolve()


def main() -> None:
    target = target_script()
    if target is None:
        print(
            "External dogfood target not configured; "
            f"set {TARGET_SCRIPT_ENV}=<script.py> to enable optional local-project scenario"
        )
        return
    if not target.exists():
        print("External dogfood target not found; skipping optional local-project scenario")
        print(target)
        return

    run([sys.executable, "-m", "build", "--wheel"])
    wheel = latest_wheel()

    with tempfile.TemporaryDirectory(prefix="pydecorators-external-dogfood-") as tmp:
        tmp_path = Path(tmp)
        runner_path = tmp_path / "run_external_dogfood.py"
        runner_path.write_text(RUNNER)
        venv_dir = tmp_path / "venv"
        run([sys.executable, "-m", "venv", str(venv_dir)])
        python = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        env = {**os.environ, "PYTHONPATH": ""}
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"], env=env)
        run([str(python), "-m", "pip", "install", str(wheel)], env=env)
        run([str(python), str(runner_path), str(target)], cwd=target.parent, env=env)

    print(f"External project dogfood passed for {wheel.name}")


if __name__ == "__main__":
    main()
