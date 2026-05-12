# Quality Gates

Use this page when you need to know which local checks protect a change before release.

## One-command local gate

```bash
hatch run full-gate
```

The Hatch alias runs the same checks listed below, in order. Prefer it for normal local release-prep verification.

## Expanded gate

```bash
./scripts/docs-policy.sh
ruff check .
ruff format --check .
mypy
python scripts/smoke_imports.py
python scripts/smoke_examples.py
pytest
python -m build
python scripts/smoke_wheel_install.py
python scripts/dogfood_local_wheel.py
python scripts/dogfood_external_project.py
```

## What each check catches

- `./scripts/docs-policy.sh`: documentation index, executable examples, release checklist, and docs-policy-only checks.
- `ruff check .`: lint issues, unsafe patterns, import order, and common Python footguns.
- `ruff format --check .`: formatting drift without rewriting files.
- `mypy`: strict type-checking for source and tests.
- `python scripts/smoke_imports.py`: public package import/export smoke test.
- `python scripts/smoke_examples.py`: loads executable documentation examples.
- `pytest`: full test suite with coverage floor and `coverage.xml` generation.
- `python -m build`: source distribution and wheel build.
- `python scripts/smoke_wheel_install.py`: clean virtualenv install/import from the built wheel.
- `python scripts/dogfood_local_wheel.py`: local wheel dogfood scenarios across the first-release decorators.
- `python scripts/dogfood_external_project.py`: wheel dogfood against a separate workspace project.

## Release posture

Passing the full gate means the local package is mechanically healthy. It does not mean publish immediately. Before TestPyPI or PyPI, re-run the package-name availability check and confirm publishing credentials/protected environments are ready.
