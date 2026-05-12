#!/usr/bin/env bash
set -euo pipefail

python -m pytest -m docs_policy --no-cov
