# [RELEASE.md](https://github.com/RusDavies/pydecorators/blob/master/RELEASE.md) — Release Checklist

Use this checklist before publishing `blakemere-wraptools` releases. The goal is to make
releases boring, repeatable, and hard to mess up. Revolutionary concept, apparently.

## Release scope

- [ ] Confirm the target version.
- [ ] Confirm the release type: patch, minor, major, or pre-1.0 compatibility-breaking release.
- [ ] Review [`TODO.md`](https://github.com/RusDavies/pydecorators/blob/master/TODO.md) for any release-blocking items.
- [ ] Confirm all intended public APIs are documented.
- [ ] Confirm all public APIs are exported from `pydecorators.__all__`.
- [ ] Confirm [`docs/PUBLIC_API.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md)
  matches the exported public API.

## Versioning

- [ ] Update `pyproject.toml` version.
- [ ] Update `src/pydecorators/__init__.py` `__version__`.
- [ ] Run the version consistency test.
- [ ] Confirm the version is not already published on PyPI/TestPyPI.

## Changelog and docs

- [ ] Update [`CHANGELOG.md`](https://github.com/RusDavies/pydecorators/blob/master/CHANGELOG.md)
  with user-facing changes.
- [ ] Confirm README examples still match implemented behavior.
- [ ] Confirm per-decorator docs are current.
- [ ] Confirm executable docs examples pass.
- [ ] Confirm [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md)
  links current documentation pages.
- [ ] Confirm public API stability notes are accurate.
- [ ] Add migration notes for breaking changes, if any.

## Persistent cache compatibility

Before publishing, check whether this release changes persistent `DiskCacheBackend` behavior:

- [ ] Confirm whether cached value semantics, payload shapes, serializers, or trust boundaries changed.
- [ ] If old persistent rows should not be reused, document the migration path: bump the cache `namespace`,
  call `cache_clear()`, call backend `clear()`, or tell users to remove the SQLite cache file.
- [ ] If old rows are still compatible, say so in release notes when persistent disk caching is affected.
- [ ] Confirm [`docs/disk_cache_backend.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md)
  cache versioning guidance is still accurate.

## Documentation maintenance

Before publishing, treat docs as release artifacts, not garnish. Run:

```bash
./scripts/docs-policy.sh
```

The script runs tests marked with the `docs_policy` pytest marker. External links are
syntax-checked by default docs policy tests. For optional network validation during release
maintenance, run:

```bash
./scripts/check_external_links.py
```

The checker uses `.external-links-ignore` for intentionally skipped third-party URLs. Keep
ignores rare and specific. Every real ignore pattern must be an HTTP(S) URL pattern, include
a host, match at least one current external docs link, be preceded by a reason comment, and
be documented in the commit that adds it. To audit checked and ignored links, run:

```bash
./scripts/check_external_links.py --syntax-only --verbose
```


The checker retries transient failures by default. If a release check is noisy, adjust retry
behavior explicitly rather than adding it to default CI:

```bash
./scripts/check_external_links.py --retries 4 --backoff 1.0
```

For a no-network local preview of the same link set, run:

```bash
./scripts/check_external_links.py --syntax-only
```

See [Quality Gates](https://github.com/RusDavies/pydecorators/blob/master/docs/quality_gates.md)
for what each command checks.

Then confirm:

- [`README.md`](https://github.com/RusDavies/pydecorators/blob/master/README.md),
  [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md),
  and [`RELEASE.md`](https://github.com/RusDavies/pydecorators/blob/master/RELEASE.md) still
  link to [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md).
- [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md) links
  every top-level page in `docs/` except itself.
- [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md) lists
  every executable example in `docs/examples/` except package markers.
- Executable examples are loaded and asserted by `tests/test_docs_examples.py`.
- Local Markdown links and heading anchors pass the docs policy tests.
- Planning/backlog docs such as [`GOAL.md`](https://github.com/RusDavies/pydecorators/blob/master/GOAL.md),
  [`PLAN.md`](https://github.com/RusDavies/pydecorators/blob/master/PLAN.md), and
  [`TODO.md`](https://github.com/RusDavies/pydecorators/blob/master/TODO.md) remain planning
  docs unless deliberately promoted to user-facing navigation.

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
- [ ] Import `pydecorators`.
- [ ] Import every public name from `pydecorators.__all__`.
- [ ] Run a tiny example using at least one decorator.

## Dogfood gate

Dogfood scenarios are part of the release gate and should pass before publishing.

```bash
python scripts/dogfood_local_wheel.py
python scripts/dogfood_external_project.py
```

Before publishing:

- [ ] Dogfood scenarios pass from an installed wheel.
- [ ] External local-project dogfood passes from an installed wheel.
- [ ] [`DOGFOOD.md`](https://github.com/RusDavies/pydecorators/blob/master/DOGFOOD.md) findings are reviewed.
- [ ] API/documentation issues found during dogfood use are resolved or explicitly deferred.


## Publishing credentials and repository setup

Do **not** publish from a random developer shell unless there is a deliberate reason. Prefer
trusted publishing from GitHub Actions so no long-lived PyPI API token has to live on a laptop,
in a chat log, or in CI secrets. Humans do keep inventing places to lose credentials; let us
not help.

### Preferred path: PyPI/TestPyPI trusted publishing

Use the trusted-publishing setup already configured for `https://github.com/RusDavies/pydecorators`
and `.github/workflows/publish.yml`:

1. Confirm the TestPyPI trusted publisher still matches:
   - project: `blakemere-wraptools`
   - owner: `RusDavies`
   - repository: `pydecorators`
   - workflow filename: `publish.yml`
   - environment: `testpypi`
2. Confirm the PyPI trusted publisher still matches the same repository/workflow with environment `pypi`.
3. Keep TestPyPI and PyPI publishing as separate jobs or separate manual approvals so a test
   release cannot accidentally become a production release with a moustache.
4. Confirm both GitHub environments still have the configured 5-minute wait timer before
   publishing. The delay is intentionally small: long enough to catch fat-fingered manual
   runs, not long enough to turn release day into geological theatre.
5. Build distributions in CI with:

   ```bash
   python -m build
   ```

6. Publish with the Python Packaging Authority publish action in `.github/workflows/publish.yml`.
   The release job publishes only files from `dist/` produced by the same workflow run.
7. After publishing to TestPyPI, install from TestPyPI in a clean environment and run the
   import/decorator smoke checks before approving PyPI.

### Fallback path: scoped API tokens

Use API tokens only if trusted publishing is unavailable. If tokens are used:

1. Create separate tokens for TestPyPI and PyPI.
2. Scope each token to only the `blakemere-wraptools` project after the project exists. For
   the first upload, a broader token may be unavoidable; rotate it immediately after the
   project is created and replace it with a project-scoped token.
3. Store tokens only in the CI secret store or a local password manager. Never commit tokens
   to this repository. Yes, even “temporarily”. Especially “temporarily”.
4. Use Twine for token publishing:

   ```bash
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*
   python -m twine upload --repository testpypi dist/*
   python -m twine upload dist/*
   ```

5. For token auth, Twine username is `__token__`; the password is the token value. Prefer
   environment variables or an interactive prompt over command-line arguments so tokens do
   not land in shell history.
6. Rotate any token that may have been exposed and remove it from every secret store where it
   is no longer needed.

### Final pre-publish checks

Immediately before publishing a new version, confirm that the built version is not already
present on PyPI/TestPyPI and verify `pyproject.toml` project URLs point to the intended
public repository. Use the repeatable checker:

   ```bash
   python scripts/check_package_name_availability.py
   ```

## Publishing

Use TestPyPI before PyPI unless there is a deliberate emergency reason not to. The included
`.github/workflows/publish.yml` workflow is manual-only (`workflow_dispatch`) and requires
the caller to choose `testpypi` or `pypi` plus the expected version. It builds, verifies,
uploads the `dist/` artifacts between jobs, and publishes through trusted publishing using
protected environments. The `testpypi` and `pypi` environments currently use a 5-minute wait
timer as a last-chance release brake.

For each release:

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
- [ ] Add post-release follow-up items to [`TODO.md`](https://github.com/RusDavies/pydecorators/blob/master/TODO.md).
- [ ] Start the next [`CHANGELOG.md`](https://github.com/RusDavies/pydecorators/blob/master/CHANGELOG.md) section.

## Package name history

The published distribution name is `blakemere-wraptools`; the import package is `pydecorators`.
Earlier planning names such as `useful-decorators`, `pydecorators`, and `py-decorators` were
not usable or were rejected during publishing setup. Keep future release docs focused on the
published distribution unless a rename is deliberately planned.

## Tagging convention

Use annotated release tags in the form `vMAJOR.MINOR.PATCH`, for example:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

Create the tag only after the release branch is merged, local verification passes, and the
package name decision is final.
