# `@require_env`

`@require_env` checks required environment variables at call time before running a sync or async function.

```python
from useful_decorators import require_env


@require_env("API_TOKEN")
def call_service() -> str:
    return "ok"
```

## Parameters

- positional names: required environment variable names.
- `validators`: optional mapping of variable name to callable. The callable receives the string value and should return `False` to reject it. Returning `True` or `None` accepts the value.
- `environ`: optional mapping used instead of `os.environ`, mainly for tests.
- `messages`: optional mapping of variable name to custom missing-variable reason string.
- `allow_empty`: whether empty string values satisfy the requirement. Defaults to `True`; set to `False` for secrets and identifiers that must be non-empty.

Invalid decorator configuration raises `ConfigurationError` at decoration time.

## Call-time behavior

Environment variables are checked when the wrapped function is called, not when it is decorated. This lets scripts load `.env` files, test fixtures patch environment values, or deployment platforms inject variables after import. Tiny mercy, because import-time environment checks are how CLIs become haunted furniture.

Missing, empty-when-disallowed, or invalid variables raise `EnvRequirementError` before the wrapped function runs. Use `messages={"API_TOKEN": "must be configured"}` when a CLI or deployment guide needs friendlier missing-variable wording.

## Examples

Multiple variables:

```python
@require_env("API_TOKEN", "REGION")
def sync_catalog() -> None:
    ...
```

Custom validators:

```python
@require_env("REGION", validators={"REGION": lambda value: value in {"ca", "us"}})
def call_regional_service() -> None:
    ...
```

Async functions are supported with the same call-time checks.


## Executable examples

Copy-pasteable examples live in `docs/examples/require_env_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate required variables,
validator failures, and async call-time checks with an injected environment.
