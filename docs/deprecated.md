# `@deprecated`

Use `@deprecated` to warn callers that a function remains available for compatibility but should no longer be used.

## Bare usage

```python
from pydecorators import deprecated


@deprecated
def old_function() -> str:
    return "still works"
```

Calling `old_function()` emits a `DeprecationWarning`.

## Configured usage

```python
from pydecorators import deprecated


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
from pydecorators import deprecated


@deprecated(replacement="fetch_new")
async def fetch_old() -> str:
    return "data"
```

## Methods

Instance methods and class methods work like normal functions:

```python
from pydecorators import deprecated


class Client:
    @deprecated(replacement="Client.fetch_new")
    def fetch_old(self) -> str:
        return "data"
```

## Classes

Explicit class deprecation is not supported yet. Decorating a class directly may appear to work because classes are callable, but the current API is designed and tested for functions and methods only.

For now, prefer deprecating the constructor helper, factory function, or individual methods. A dedicated class-deprecation feature should be designed separately so it can preserve class behavior and typing without unpleasant metaclass goblinry.

## Warning filters

`@deprecated` emits `DeprecationWarning` by default. Python often hides `DeprecationWarning` outside `__main__` and test contexts, so users may not see these warnings unless their warning filters show them.

For tests, use `pytest.warns` or enable warnings explicitly:

```bash
python -W default -m pytest
```

For applications, choose the warning policy deliberately:

```python
import warnings

warnings.simplefilter("default", DeprecationWarning)
```

Library authors should usually keep the default `DeprecationWarning`; application authors can pass a custom `category` if they need a louder warning.

## Type-checking examples

Bare usage preserves the wrapped function signature:

```python
from pydecorators import deprecated


@deprecated
def old_add(left: int, right: int) -> int:
    return left + right

result: int = old_add(1, 2)
```

Configured usage also preserves the wrapped function signature:

```python
from pydecorators import deprecated


@deprecated("Use add instead.", replacement="add")
def old_add(left: int, right: int) -> int:
    return left + right

result: int = old_add(1, 2)
```

## Parameters

- `reason`: optional human-readable explanation.
- `replacement`: optional replacement function/API name.
- `version`: optional version where deprecation started.
- `remove_in`: optional planned removal version.
- `category`: warning category, default `DeprecationWarning`.
- `stacklevel`: warning stack level, default `2`.
