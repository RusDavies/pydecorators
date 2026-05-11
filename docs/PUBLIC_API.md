# Public API Policy

This project keeps its public API deliberately small.

## Public API

The public API is anything exported from `useful_decorators.__all__` and documented in the README or `docs/`.

Current public API:

- `deprecated`
- `UsefulDecoratorsError`
- `ConfigurationError`
- `RateLimitExceeded`
- `FunctionTimedOut`

## Internal API

Modules or names prefixed with `_` are internal. They may change without deprecation while the project is pre-1.0.

Examples:

- `useful_decorators._core`
- `useful_decorators._typing`

## Stability before `1.0`

Until `1.0`, public APIs may still change, but breaking changes should be:

- documented in `CHANGELOG.md`
- reflected in examples and tests
- minimized unless they fix a design mistake

## Stability after `1.0`

After `1.0`, public API changes should follow semantic versioning:

- patch releases: bug fixes only
- minor releases: backward-compatible features
- major releases: breaking changes

Deprecated APIs should generally warn for at least one minor release before removal unless keeping them would be unsafe or severely broken.

## Compatibility hardening

CI must include the minimum supported Python version from `pyproject.toml`. For the current project metadata, that means Python 3.11 must stay in the workflow matrix until support policy changes.
