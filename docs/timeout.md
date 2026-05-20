# `@timeout`

`@timeout` fails an async function when it does not finish before a configured deadline.

```python
from pydecorators import timeout


@timeout(seconds=2)
async def fetch_user(user_id: str) -> dict[str, object]:
    ...
```

## Parameters

- `seconds`: timeout duration. Must be greater than zero.
- `message`: optional custom exception message.
- `exception`: exception type raised on timeout. Defaults to `FunctionTimedOut`.

Invalid configuration raises `ConfigurationError` at decoration time.

Custom exception types must be constructible with a single message string, for example
`CustomTimeout("operation timed out")`. Exception classes that require additional
constructor arguments are not supported by `@timeout`; wrap them in a simple timeout
exception type instead of relying on unusual constructor signatures.

## Async behavior

The first implementation is intentionally async-only and uses `asyncio.wait_for`. If the wrapped coroutine exceeds the deadline, `@timeout` raises `FunctionTimedOut` by default. The underlying coroutine is cancelled by `asyncio.wait_for` according to normal asyncio semantics.

## Sync behavior

Synchronous timeout support is deliberately not implemented in the current release. Decorating a sync function raises `ConfigurationError`.

The rejected sync strategies were:

- Unix `signal` alarms: process-global, main-thread-only, and awkward in libraries.
- Worker threads: cannot safely stop arbitrary Python code and can leave background work running after the caller sees a timeout.
- Pretending sync timeouts are simple: a traditional way to manufacture production gremlins.

If sync timeout support is ever added, it needs an explicit design with documented platform and cancellation limitations. The current decision record is [`sync_timeout_decision.md`](sync_timeout_decision.md).

## Failure modes to watch for

`@timeout` is a deadline mechanism, not a safe way to erase work from existence.

- Async cancellation is cooperative. If the wrapped coroutine suppresses cancellation,
  performs blocking sync I/O, or leaves background tasks running, the caller can still
  see a timeout while other work continues elsewhere. That is how "the request failed"
  becomes "the side effect happened anyway", a classic little crime scene.
- Put `@timeout` outside `@retry` when the user-visible operation has one budget. Put it
  inside `@retry` only when each attempt should get its own budget and the longer total
  runtime is acceptable.
- Do not use timeout as an idempotency control. If the operation creates orders, sends
  messages, charges cards, or mutates external state, keep the operation's own
  idempotency key or deduplication strategy.
- Avoid catching `FunctionTimedOut` and immediately retrying in outer application code
  unless you have checked the total deadline. Otherwise the decorator is just producing
  expensive pauses between attempts.

## Examples

Custom message and exception:

```python
class ExternalCallTimedOut(Exception):
    pass


@timeout(seconds=1.5, message="external call timed out", exception=ExternalCallTimedOut)
async def call_external_service() -> str:
    ...
```


## Executable examples

Copy-pasteable async examples live in `docs/examples/timeout_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate successful completion,
timeout handling, and custom timeout exceptions without relying on sync timeout
tricks.
