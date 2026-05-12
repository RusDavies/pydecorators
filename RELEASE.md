# RELEASE.md — Release Checklist

Use this checklist before publishing `blakemere-decorators` releases. The goal is to make releases boring, repeatable, and hard to mess up. Revolutionary concept, apparently.

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
- [ ] Confirm `docs/index.md` links current documentation pages.
- [ ] Confirm public API stability notes are accurate.
- [ ] Add migration notes for breaking changes, if any.

## Persistent cache compatibility

Before publishing, check whether this release changes persistent `DiskCacheBackend` behavior:

- [ ] Confirm whether cached value semantics, payload shapes, serializers, or trust boundaries changed.
- [ ] If old persistent rows should not be reused, document the migration path: bump the cache `namespace`, call `cache_clear()`, call backend `clear()`, or tell users to remove the SQLite cache file.
- [ ] If old rows are still compatible, say so in release notes when persistent disk caching is affected.
- [ ] Confirm `docs/disk_cache_backend.md` cache versioning guidance is still accurate.

## Documentation maintenance

Before publishing, treat docs as release artifacts, not garnish. Run:

```bash
./scripts/docs-policy.sh
```

The script runs tests marked with the `docs_policy` pytest marker. External links are syntax-checked by default docs policy tests. For optional network validation during release maintenance, run:

```bash
./scripts/check_external_links.py
```

The checker uses `.external-links-ignore` for intentionally skipped third-party URLs. Keep ignores rare and specific. Every real ignore pattern must be an HTTP(S) URL pattern, include a host, match at least one current external docs link, be preceded by a reason comment, and be documented in the commit that adds it. To audit checked and ignored links, run:

```bash
./scripts/check_external_links.py --syntax-only --verbose
```


The checker retries transient failures by default. If a release check is noisy, adjust retry behavior explicitly rather than adding it to default CI:

```bash
./scripts/check_external_links.py --retries 4 --backoff 1.0
```

For a no-network local preview of the same link set, run:

```bash
./scripts/check_external_links.py --syntax-only
```

Then confirm:

- `README.md`, `CONTRIBUTING.md`, and `RELEASE.md` still link to `docs/index.md`.
- `docs/index.md` links every top-level page in `docs/` except itself.
- `docs/index.md` lists every executable example in `docs/examples/` except package markers.
- Executable examples are loaded and asserted by `tests/test_docs_examples.py`.
- Local Markdown links and heading anchors pass the docs policy tests.
- Planning/backlog docs such as `GOAL.md`, `PLAN.md`, and `TODO.md` remain planning docs unless deliberately promoted to user-facing navigation.

## Quality gates

Run the full local verification gate:

```bash
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

Then confirm:

- [ ] Lint passes.
- [ ] Format check passes.
- [ ] Type check passes.
- [ ] Import smoke test passes.
- [ ] Examples smoke test passes.
- [ ] Tests pass.
- [ ] Coverage remains above the configured floor and reports are generated.
- [ ] Package build succeeds.
- [ ] Clean-wheel install smoke test passes.
- [ ] Dogfood wheel scenarios pass.
- [ ] Built artifacts are not committed accidentally.

## Install smoke tests

Run:

```bash
python scripts/smoke_wheel_install.py
```

Then confirm:

- [ ] Create a clean virtual environment.
- [ ] Install the built wheel locally.
- [ ] Import `useful_decorators`.
- [ ] Import every public name from `useful_decorators.__all__`.
- [ ] Run a tiny example using at least one decorator.

## Dogfood gate

Publishing is intentionally paused until local dogfood scenarios have run and findings in `DOGFOOD.md` are reviewed.

```bash
python scripts/dogfood_local_wheel.py
python scripts/dogfood_external_project.py
```

Before TestPyPI/PyPI:

- [ ] Dogfood scenarios pass from an installed wheel.
- [ ] External local-project dogfood passes from an installed wheel.
- [ ] `DOGFOOD.md` findings are reviewed.
- [ ] API/documentation issues found during dogfood use are resolved or explicitly deferred.

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

## Package name availability

As of 2026-05-12, the PyPI project name `useful-decorators` is already occupied by another project. Russ chose `blakemere-decorators` as the replacement distribution name, and PyPI/TestPyPI returned 404 Not Found for that name when checked before updating `pyproject.toml`. Re-check availability immediately before publishing because package names are mutable external state, annoyingly.

## Tagging convention

Use annotated release tags in the form `vMAJOR.MINOR.PATCH`, for example:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

Create the tag only after the release branch is merged, local verification passes, and the package name decision is final.
