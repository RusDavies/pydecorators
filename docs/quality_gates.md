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


External link ignore patterns must normally match at least one current docs link. During staged release-maintenance edits, `python scripts/check_external_links.py --allow-stale-ignores` permits temporary unmatched ignore patterns; remove the escape hatch before treating the ignore list as final.

### External link ignore wildcards

`.external-links-ignore` uses Python `fnmatch`-style URL patterns. Use full HTTP(S) URL shapes such as `https://vendor.example.com/docs/*`; `*` matches within the URL string, including path separators, and matching is case-sensitive. Each non-comment pattern must be preceded by a reason comment so temporary ignores do not fossilize into mystery sediment. Reason comments may include `expires: YYYY-MM-DD`; expired ignore patterns fail the checker until they are removed or deliberately renewed.

External link release checks also support `--json` for quiet machine-readable summaries in automation. Combine it with `--syntax-only` for deterministic dry runs or with live checks immediately before release.

Non-HTTP Markdown links are rejected by default during external-link checks. If a docs page intentionally needs a scheme such as `mailto`, pass `--allow-scheme mailto` and document why the link belongs in public docs.
