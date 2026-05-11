# Contributing

## Adding a new decorator

Use this checklist when adding a decorator. Yes, it is mildly bossy. That is the point.

1. Update `TODO.md` or the relevant design document with the intended behavior.
2. Decide whether the decorator supports bare usage, configured usage, or both.
3. Add implementation under `src/useful_decorators/`.
4. Use shared helpers from `useful_decorators._core` where applicable:
   - `is_async_callable`
   - `mirror_metadata`
   - `monotonic`
   - `sync_sleep`
   - `async_sleep`
   - configuration validators
5. Preserve wrapped function metadata.
6. Support async functions where practical, or document why not.
7. Export the decorator from `useful_decorators.__init__` and `__all__` only when it is ready to be public.
8. Add tests for:
   - normal behavior
   - invalid configuration
   - metadata preservation
   - sync and async paths, if supported
   - composition or edge cases when relevant
9. Add README and per-decorator documentation examples.
10. Add executable examples under `docs/examples/` when useful.
11. Run the full verification gate:

```bash
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

## Public API rule

If a name is in `useful_decorators.__all__`, it is public. Public names need tests and documentation.

If a helper is not meant for users, keep it in an underscore-prefixed module.

## Executable documentation examples

When adding runnable docs examples, put them under `docs/examples/` and use the naming pattern `<topic>_examples.py`, for example `deprecated_examples.py` or `disk_cache_backend_examples.py`.

Keep example modules importable without side effects beyond defining small functions/classes. Public top-level example functions should be directly asserted in `tests/test_docs_examples.py`; if a file is intentionally not executable, document why and exempt it explicitly in the relevant policy test.

After adding a new example file:

1. Link it from `docs/index.md`.
2. Load it through `load_docs_example(...)` in `tests/test_docs_examples.py`.
3. Add at least one assertion for each public top-level example function.
4. Run the full verification gate.

## Adding or changing documentation files

When adding or changing docs files, use this checklist before calling the slice done:

1. Link new top-level `docs/*.md` pages from `docs/index.md`, unless the file is intentionally exempt and the docs policy test says why.
2. Link new executable examples under `docs/examples/` from `docs/index.md`.
3. Add or update assertions in `tests/test_docs_examples.py` for public top-level example functions.
4. Add `pytest.mark.docs_policy` coverage when the change introduces a new documentation rule.
5. Run `./scripts/docs-policy.sh` before the full verification gate.

If a planning/backlog file such as `GOAL.md`, `PLAN.md`, or `TODO.md` becomes user-facing navigation, update the root documentation link policy at the same time.

## Documentation policy tests

Use the `docs_policy` pytest marker for tests that guard documentation maintenance rather than runtime behavior. Mark tests with `@pytest.mark.docs_policy` or a module-level `pytestmark = pytest.mark.docs_policy` when they check things like:

- `docs/index.md` coverage and navigation rules
- executable documentation example indexing, naming, loading, or assertion coverage
- Markdown local-link or heading-anchor validation
- root documentation link policy
- release-checklist documentation maintenance rules

Do not use `docs_policy` for normal decorator behavior, backend behavior, public API exports, or version checks unless the test is specifically about documentation upkeep.

Run documentation policy checks with:

```bash
./scripts/docs-policy.sh
```

## Root documentation links

Root docs that help users or contributors navigate the project should link to `docs/index.md`. Today that means:

- `README.md`
- `CONTRIBUTING.md`
- `RELEASE.md`

Planning/backlog docs such as `GOAL.md`, `PLAN.md`, and `TODO.md` are not required to link the docs index unless they grow into user-facing navigation docs.
