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
