#!/usr/bin/env bash
set -euo pipefail

python -m pytest \
  tests/test_public_api_policy.py \
  tests/test_docs_examples.py \
  tests/test_release_checklist.py
