# PLAN.md — Python Decorators Library Project Plan

## Phase 1 — Product Definition

Clarify the library's position, target users, and first-release scope.

### Outcomes

- Confirm package name and import namespace.
- Choose supported Python versions.
- Decide first-release decorators.
- Define compatibility expectations for sync and async functions.
- Decide dependency posture: standard library first, optional integrations later.

### Recommended Decisions

- Package/import namespace: `useful_decorators` or `pydecorators` rather than `python_decorators`, because the latter is generic and may be awkward on PyPI.
- Python support: Python 3.10+ or 3.11+.
- First release: `retry`, `cache_result`, `rate_limit`, `timeout`, `deprecated`.
- Later releases: `log_calls`, `measure_time`, `validate_types`, `circuit_breaker`, `require_env`.

## Phase 2 — Repository and Tooling Setup

Create a clean Python package foundation.

### Outcomes

- `pyproject.toml` using modern packaging.
- Source layout under `src/`.
- Tests under `tests/`.
- Development tooling for formatting, linting, typing, and tests.
- Initial README and documentation structure.

### Candidate Tooling

- Packaging/build: `hatchling` or `setuptools`.
- Tests: `pytest` and `pytest-asyncio`.
- Lint/format: `ruff`.
- Type checking: `mypy` or `pyright`.
- Coverage: `coverage.py` or `pytest-cov`.

## Phase 3 — API Design

Design the public API before implementation.

### Outcomes

- Consistent decorator signatures.
- Clear naming conventions.
- Shared internal utilities for wrapping sync/async functions.
- Standard error types where useful.
- Documentation examples for each decorator before coding.

### API Principles

- Decorators should work with and without parentheses where reasonable.
- Preserve function metadata using `functools.wraps`.
- Preserve useful typing using `ParamSpec` and `TypeVar`.
- Avoid global mutable behavior unless explicitly configured.
- Make async support explicit and tested.

## Phase 4 — Implement First Decorator Set

Build the first release decorators one at a time, with tests and docs for each.

### Decorators

1. `@deprecated`
   - Lowest risk and useful immediately.
   - Supports message, replacement, version, removal version, and warning category.

2. `@cache_result`
   - TTL cache, max size, custom key function, optional cache clearing.
   - Sync and async support if practical.

3. `@retry`
   - Max attempts, delay, exponential backoff, jitter, exception filters, before/after callbacks.
   - Sync and async support.

4. `@rate_limit`
   - Calls per time window.
   - Blocking or raising mode.
   - Optional key function.

5. `@timeout`
   - Async timeout via `asyncio.wait_for`.
   - Sync timeout strategy requires careful platform decisions; avoid unsafe thread killing.

## Phase 5 — Testing Strategy

Build confidence without making the tests brittle.

### Outcomes

- Unit tests for every decorator.
- Async tests for async-capable decorators.
- Edge case tests for invalid configuration.
- Timing-sensitive tests designed with tolerances.
- Tests proving function metadata preservation.
- Tests proving decorators compose correctly.

## Phase 6 — Documentation and Examples

Make the project easy to understand and adopt.

### Outcomes

- README with quick-start examples.
- Per-decorator documentation.
- Practical examples for APIs, CLIs, scripts, and background jobs.
- Security notes for logging and environment/config decorators.
- Migration/versioning notes once releases begin.

## Phase 7 — Packaging and Release Prep

Prepare for a clean public release.

### Outcomes

- Package metadata complete.
- License selected.
- Changelog started.
- Versioning policy documented.
- CI workflow added.
- PyPI publishing path defined.

## Phase 8 — Post-v0.1 Expansion

Expand beyond the starter set based on usefulness and user feedback.

### Candidate Follow-Ups

- `@log_calls` with redaction support.
- `@measure_time` with callback/metrics hooks.
- `@validate_types` using type hints.
- `@circuit_breaker` for service clients.
- `@require_env` for scripts and CLIs.
- Optional integrations with OpenTelemetry, Redis, or structlog.

## Risks and Mitigations

### Timing Bugs

Decorators like `timeout`, `rate_limit`, and `retry` can produce flaky tests.

Mitigation: use injectable clocks/sleep functions internally where possible.

### Unsafe Timeout Semantics

Killing synchronous Python code safely is hard.

Mitigation: document limitations clearly. Prefer async support first and conservative sync behavior.

### Secret Leakage

Logging decorators can accidentally expose credentials.

Mitigation: make redaction a first-class feature and keep logs minimal by default.

### Scope Creep

This could become a framework if allowed to eat too many vegetables.

Mitigation: keep the core small, add optional integrations later.
