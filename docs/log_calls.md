# `@log_calls`

`@log_calls` logs call start, completion duration, optional argument metadata, optional summarized return values, and exceptions for sync and async functions.

```python
from useful_decorators import log_calls


@log_calls()
def rebuild_index() -> None:
    ...
```

## Parameters

- `logger`: optional `logging.Logger`. Defaults to a logger named after the wrapped function module.
- `level`: integer logging level. Defaults to `logging.INFO`.
- `include_args`: include positional args and keyword args in the start log. Defaults to `False`.
- `include_result`: include the return value, or summarized return value, in the finish log. Defaults to `False`.
- `redact_args`: argument names to replace with `"<redacted>"` when `include_args=True`; this covers keyword arguments and positional arguments whose parameter names can be resolved from the wrapped function signature.
- `summarize_result`: optional callable used to turn the return value into a smaller or safer logged summary. Async wrappers await the summary if the callable returns an awaitable.
- `log_exceptions`: log failures with traceback via `logger.exception`. Defaults to `True`.
- `clock`: injectable clock for duration tests.

Invalid configuration raises `ConfigurationError` at decoration time.

## Structured log fields

Every emitted record includes `useful_decorators_function` and `useful_decorators_event` (`"started"`, `"finished"`, or `"failed"`) in `logging`'s `extra` data. Finished and failed records also include `useful_decorators_duration_seconds` and `useful_decorators_success` so log pipelines can filter or aggregate without parsing the human-readable message.

Durations use Python's monotonic clock by default, not wall-clock time. That keeps call durations stable across NTP corrections, daylight saving changes, and other clock adjustments. Use `clock=` for tests or custom runtimes, and prefer a monotonic-style source in production.

## Security notes

Logging arguments and return values is risky. The safe default is metadata-only logging: function name, start, finish, duration, and exceptions. Do not enable `include_args` or `include_result` on functions that handle credentials, tokens, personal data, payment data, medical data, tenant secrets, or large payloads unless the logging policy has been reviewed.

`redact_args` redacts named parameters at the top level only. It does not inspect nested dictionaries, objects, headers, serialized payloads, varargs contents, or return values. That is deliberate: fake automatic secret detection is how secrets end up preserved forever in log aggregation with a tiny bow on top.

When return values are useful for diagnostics, prefer `summarize_result` over raw `include_result=True`. Summaries should expose counts, statuses, IDs already safe for logs, or coarse shapes rather than full payloads.

## Examples

Redacting keyword arguments:

```python
@log_calls(include_args=True, redact_args={"password", "api_key"})
def authenticate(*, username: str, password: str, api_key: str) -> bool:
    ...
```

Summarizing results:

```python
@log_calls(include_result=True, summarize_result=lambda result: {"count": len(result)})
def list_jobs() -> list[str]:
    ...
```

Async functions work the same way:

```python
@log_calls()
async def refresh_user(user_id: str) -> None:
    ...
```


## Executable examples

Copy-pasteable examples live in `docs/examples/log_calls_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate argument redaction,
result summarization, and async logging using an in-memory test handler so the
examples do not depend on global logging configuration.
