# `@validate_types`

`@validate_types` performs small, standard-library runtime checks against function annotations.

```python
from pydecorators import validate_types


@validate_types()
def greet(name: str, excited: bool = False) -> str:
    return f"hello {name}{'!' if excited else ''}"
```

## Parameters

- `validate_return`: when `True`, validate the annotated return value. Defaults to `False`.
- `deep`: when `True`, validate supported container contents for `list`, `dict`, `tuple`, `set`, and `frozenset`. Defaults to `False`.

Invalid configuration raises `ConfigurationError` at decoration time.

## Supported checks

The first implementation intentionally supports a conservative subset:

- basic runtime classes such as `str`, `int`, `float`, `bool`, and custom classes
- `None`
- `Optional` / union syntax such as `str | None` or `int | str`
- `Literal[...]` value membership checks
- `Annotated[...]` by validating the wrapped base type and ignoring metadata
- common container origins such as `list[int]`, `dict[str, object]`, `tuple[...]`, `set[...]`, and `frozenset[...]`
- `Any`, which always passes

Container checks are shallow by default. `list[int]` checks that the value is a list, not that every element is an `int`. Pass `deep=True` to recursively validate supported container contents when that extra strictness is useful. Deep mode remains deliberately small; it is not data coercion, schema validation, or a replacement for a real validation library wearing a fake lab coat.

Unsupported or complex annotations are treated as pass-through rather than failing closed. This keeps the decorator useful for simple scripts and tests without pretending it fully implements Python's typing system.

## Errors

Argument validation failures raise `ValidationError` with the function name, argument name, expected type, and actual runtime type.

Return validation failures raise `ValidationError` with the function name, expected return type, and actual runtime type.

`ValidationError` inherits from both `TypeError` and `UsefulDecoratorsError`, so existing callers can catch ordinary type failures while package-aware callers can distinguish validation mismatches from unrelated `TypeError`s.

## Async support

Async functions are supported with the same argument and optional return validation behavior.

## Limitations

`@validate_types` is not a schema validator and not a security boundary. Even in `deep=True` mode, it does not validate protocols, typed dictionaries, callables, arbitrary generics, constrained values beyond explicit `Literal[...]` membership, data coercion, or user-defined validation rules. Use Pydantic, attrs validators, dataclasses plus explicit checks, or domain-specific validation when that level of enforcement matters.


## Executable examples

Copy-pasteable examples live in `docs/examples/validate_types_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate argument checks,
optional return validation, and async support while keeping the shallow-validation
limitations explicit.
