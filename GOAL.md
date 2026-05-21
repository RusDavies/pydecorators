# [GOAL.md](https://github.com/RusDavies/pydecorators/blob/master/GOAL.md) — Python Decorators Library

## Project Goal

Build a small, well-documented Python library of useful decorators that solve common everyday problems for Python developers without forcing them into a large framework.

The library should feel simple enough for scripts, reliable enough for production code, and clear enough that developers can understand what each decorator does without spelunking through a swamp of cleverness. Python decorators already provide enough wizardry; we do not need to add fog machines.

## Core Product Idea

Create a package tentatively named `python-decorators` that provides a focused set of high-value decorators for:

- reliability
- performance
- observability
- validation
- API/client safety
- developer ergonomics

The initial library should prioritize decorators that are broadly useful across backend apps, CLIs, automation scripts, data workflows, and service clients.

## Initial Decorator Candidates

The first version should evaluate and implement a starter set from these 10 popular candidates:

1. `@retry` — retry failing calls with backoff, jitter, and exception filters.
2. `@timeout` — enforce maximum runtime for sync and async functions.
3. `@rate_limit` — limit call frequency globally or by key.
4. `@cache_result` — cache results with TTL, max size, and custom key support.
5. `@validate_types` — validate runtime arguments from type hints.
6. `@log_calls` — log calls, results, duration, and exceptions safely.
7. `@measure_time` — measure execution time and emit metrics/logs/callbacks.
8. `@deprecated` — warn users about deprecated APIs with replacement guidance.
9. `@circuit_breaker` — prevent repeated calls to failing dependencies.
10. `@require_env` — require environment variables/config before execution.

## Target Users

- Python application developers
- Backend/API developers
- DevOps and automation engineers
- Data engineers writing operational scripts
- Library authors who want reusable decorator utilities
- Teams that want lightweight reliability/observability helpers without adopting a full framework

## Success Criteria

A successful first release should have:

- A clear package structure.
- A polished public API.
- Strong support for both sync and async functions where practical.
- Type hints and compatibility with modern Python.
- Good documentation and examples for every decorator.
- Tests covering normal, edge, and failure paths.
- A minimal dependency footprint.
- Safe defaults, especially for logging and secrets.
- Packaging ready for PyPI publication.

## Design Principles

- **Simple by default, configurable when needed.** Common cases should take one line.
- **Do not hide dangerous behavior.** Timeouts, retries, and logging must be explicit and predictable.
- **Sync and async should both matter.** Python users increasingly mix both.
- **No surprise secret leaks.** Logging decorators must support redaction.
- **Composable where possible.** Decorators should not fight each other.
- **Production-friendly, not enterprise-bloat-friendly.** Useful, typed, tested, boring in the best possible way.

## Non-Goals for the First Release

- Building a full framework.
- Replacing Pydantic, Tenacity, structlog, OpenTelemetry, or Redis.
- Supporting every historical Python version.
- Adding distributed infrastructure dependencies by default.
- Magical auto-configuration from global state.

## Suggested First Release Scope

For `v0.1.0`, implement a tight starter set:

- `@retry`
- `@cache_result`
- `@rate_limit`
- `@timeout`
- `@deprecated`

Then add observability and advanced resilience decorators in follow-up releases.
