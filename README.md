# Useful Decorators

A focused Python library of useful decorators for everyday reliability, caching, rate limiting, timeouts, and developer ergonomics.

The goal is to provide small, typed, well-tested decorators that work in scripts, CLIs, services, and libraries without requiring a framework or a dependency shrubbery.

## Planned first release

The initial `v0.1.0` scope is:

- `@deprecated` — implemented
- `@cache_result`
- `@retry`
- `@rate_limit`
- `@timeout`


## Quick example

```python
from useful_decorators import deprecated


@deprecated("Kept for compatibility.", replacement="new_function", version="0.1.0")
def old_function() -> str:
    return "still works"
```

## Development status

Pre-alpha. The project foundation exists and `@deprecated` is implemented.

Warnings use `DeprecationWarning` by default, which Python may hide depending on warning filters. See `docs/deprecated.md` for details.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

## Public API and contributing

See `docs/PUBLIC_API.md` for the public API policy and `CONTRIBUTING.md` for the new-decorator checklist. Executable documentation examples live under `docs/examples/`.
