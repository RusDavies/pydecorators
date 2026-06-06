#!/usr/bin/env bash
set -euo pipefail

python -m pytest -m docs_policy --no-cov
python scripts/check_docs_example_index.py
python scripts/check_workflow_action_pins.py
