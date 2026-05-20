# API Design Notes

These notes capture the API choices that should stay consistent as the library grows.

Decorator libraries become messy when every wrapper invents its own rules for naming,
configuration, typing, metadata, and sync/async behavior. The result is not flexibility;
it is archaeology with stack traces. This document keeps those decisions explicit so a
new decorator feels like part of the same package rather than a clever one-off that
escaped review.

## Public naming conventions

- Decorators use short, verb-oriented snake_case names: `retry`, `timeout`, `rate_limit`, `cache_result`, `deprecated`.
- Public exceptions use descriptive PascalCase names and inherit from `UsefulDecoratorsError`.
- Internal helpers live in underscore-prefixed modules and are not part of the public API.
- Package exports should be deliberate. A decorator becomes public only when added to `pydecorators.__all__` and documented.

## Bare vs configured usage

Decorators should support both bare and configured usage only when the bare form has safe, obvious defaults.

Good candidates:

- `@deprecated`
- `@log_calls`, if added later with minimal logging defaults

Configured-only candidates:

- `@retry`, because retry policy should be explicit
- `@timeout`, because duration must be explicit
- `@rate_limit`, because allowance/window must be explicit
- `@cache_result`, because cache semantics should be obvious at call site

## Shared typing

Decorator implementations should use shared `ParamSpec` and `TypeVar` helpers from `pydecorators._typing` so wrapped call signatures remain as precise as practical.

## Sync and async support

- Use `is_async_callable()` to choose sync vs async wrappers.
- Preserve metadata in both paths.
- Test sync and async behavior separately.
- Prefer injectable clock/sleep functions for timing-sensitive decorators.

## Configuration validation

- Validate decorator configuration at decoration time, not first call, where practical.
- Raise `ConfigurationError` for invalid package-level decorator configuration.
- Keep validation messages direct and specific.

## Metadata preservation

Every decorator must preserve at least:

- `__name__`
- `__doc__`
- `__module__`
- `__qualname__`
- `__annotations__`
- `__wrapped__`

Use `mirror_metadata()` or `functools.wraps` directly if there is a good reason.
