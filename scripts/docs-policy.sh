#!/usr/bin/env bash
set -euo pipefail

python -m pytest \
  tests/test_docs_policy.py \
  tests/test_docs_examples.py \
  tests/test_release_checklist.py
