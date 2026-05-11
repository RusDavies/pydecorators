# `@deprecated`

Use `@deprecated` to warn callers that a function remains available for compatibility but should no longer be used.

## Bare usage

```python
from useful_decorators import deprecated


@deprecated
def old_function() -> str:
    return "still works"
```

Calling `old_function()` emits a `DeprecationWarning`.

## Configured usage

```python
from useful_decorators import deprecated


@deprecated(
    "The old API shape is kept only for compatibility.",
    replacement="new_function",
    version="0.3.0",
    remove_in="1.0.0",
)
def old_function() -> str:
    return "still works"
```

The warning message includes:

- the deprecated function name
- the version where deprecation began, if provided
- the planned removal version, if provided
- the replacement, if provided
- the reason, if provided

## Async functions

`@deprecated` supports async functions too:

```python
@deprecated(replacement="fetch_new")
async def fetch_old() -> str:
    return "data"
```

## Parameters

- `reason`: optional human-readable explanation.
- `replacement`: optional replacement function/API name.
- `version`: optional version where deprecation started.
- `remove_in`: optional planned removal version.
- `category`: warning category, default `DeprecationWarning`.
- `stacklevel`: warning stack level, default `2`.
