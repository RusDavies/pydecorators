# RELEASE.md — Release Checklist

Use this checklist before publishing `useful-decorators` releases. The goal is to make releases boring, repeatable, and hard to mess up. Revolutionary concept, apparently.

## Release scope

- [ ] Confirm the target version.
- [ ] Confirm the release type: patch, minor, major, or pre-1.0 compatibility-breaking release.
- [ ] Review `TODO.md` for any release-blocking items.
- [ ] Confirm all intended public APIs are documented.
- [ ] Confirm all public APIs are exported from `useful_decorators.__all__`.
- [ ] Confirm `docs/PUBLIC_API.md` matches the exported public API.

## Versioning

- [ ] Update `pyproject.toml` version.
- [ ] Update `src/useful_decorators/__init__.py` `__version__`.
- [ ] Run the version consistency test.
- [ ] Confirm the version is not already published on PyPI/TestPyPI.

## Changelog and docs

- [ ] Update `CHANGELOG.md` with user-facing changes.
- [ ] Confirm README examples still match implemented behavior.
- [ ] Confirm per-decorator docs are current.
- [ ] Confirm executable docs examples pass.
- [ ] Confirm public API stability notes are accurate.
- [ ] Add migration notes for breaking changes, if any.

## Quality gates

Run the full local verification gate:

```bash
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

Then confirm:

- [ ] Lint passes.
- [ ] Format check passes.
- [ ] Type check passes.
- [ ] Tests pass.
- [ ] Coverage remains acceptable.
- [ ] Package build succeeds.
- [ ] Built artifacts are not committed accidentally.

## Install smoke tests

- [ ] Create a clean virtual environment.
- [ ] Install the built wheel locally.
- [ ] Import `useful_decorators`.
- [ ] Import every public name from `useful_decorators.__all__`.
- [ ] Run a tiny example using at least one decorator.

## Publishing

For first release, use TestPyPI before PyPI.

- [ ] Publish to TestPyPI.
- [ ] Install from TestPyPI in a clean environment.
- [ ] Run import/decorator smoke tests from TestPyPI install.
- [ ] Publish to PyPI.
- [ ] Install from PyPI in a clean environment.
- [ ] Tag the release in git.
- [ ] Push the tag.

## Post-release

- [ ] Verify package page metadata and links render correctly.
- [ ] Verify README renders correctly on PyPI.
- [ ] Create a GitHub release if the repository is public.
- [ ] Add post-release follow-up items to `TODO.md`.
- [ ] Start the next `CHANGELOG.md` section.
