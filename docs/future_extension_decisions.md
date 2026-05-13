# Future Extension Decisions

This page records small backlog decisions that are worth making explicit without turning every maybe-useful idea into public API surface.

## JSON datetime/bytes adapter helper

Keep the datetime/bytes JSON adapter as an executable documentation recipe for now. Do not promote it into a reusable helper until more than one maintained example or user workflow needs the exact same tagged format.

Because the adapter remains documentation guidance rather than public API, there is no public tag/version compatibility promise yet. Compatibility tests should be added only if a tagged adapter becomes exported API.

## Planning document navigation

Do not add `TODO.md` or planning notes to the public documentation navigation. If TODO/PLAN files become website pages later, add navigation policy tests at the same time so draft-only planning does not leak into release docs by accident.

## Docs-policy CI path filtering

Keep docs-policy in the normal CI gate for now. Path filtering can save a little time, but it also risks hiding drift in docs index and examples policy checks. Revisit only if CI time becomes materially annoying.

## Retry hook context objects

Keep retry hooks on the current simple signatures:

- `before_attempt(attempt_number)`
- `after_attempt(attempt_number, exception_or_none)`

Do not add richer context objects until callers need delay, elapsed-time, exception-classification, or sleep-decision metadata. If that happens, prefer additive hook names or a backwards-compatible adapter rather than changing the existing callable contract.

## Circuit breaker fallback callbacks

Keep fallback behavior outside `@circuit_breaker` for now. Callers can catch `CircuitBreakerOpen` or compose their own wrapper around a decorated function. Built-in fallback callbacks should wait for concrete user demand because fallback semantics quickly become application policy: stale cache, default value, queued work, or degraded service response all mean different things.

## Redis conformance suite timing

The backend conformance suite is ready for future storage backends, but Redis should only be added to it when `RedisCacheBackend` exists. Until then, tests should continue asserting that the base package imports without Redis installed and that no accidental public Redis module appears.
