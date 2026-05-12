# `@timeout`

`@timeout` fails an async function when it does not finish before a configured deadline.

```python
from useful_decorators import timeout


@timeout(seconds=2)
async def fetch_user(user_id: str) -> dict[str, object]:
    ...
```

## Parameters

- `seconds`: timeout duration. Must be greater than zero.
- `message`: optional custom exception message.
- `exception`: exception type raised on timeout. Defaults to `FunctionTimedOut`.

Invalid configuration raises `ConfigurationError` at decoration time.

## Async behavior

The first implementation is intentionally async-only and uses `asyncio.wait_for`. If the wrapped coroutine exceeds the deadline, `@timeout` raises `FunctionTimedOut` by default. The underlying coroutine is cancelled by `asyncio.wait_for` according to normal asyncio semantics.

## Sync behavior

Synchronous timeout support is deliberately not implemented for the first release. Decorating a sync function raises `ConfigurationError`.

The rejected sync strategies were:

- Unix `signal` alarms: process-global, main-thread-only, and awkward in libraries.
- Worker threads: cannot safely stop arbitrary Python code and can leave background work running after the caller sees a timeout.
- Pretending sync timeouts are simple: a traditional way to manufacture production gremlins.

If sync timeout support is ever added, it needs an explicit design with documented platform and cancellation limitations.

## Examples

Custom message and exception:

```python
class ExternalCallTimedOut(Exception):
    pass


@timeout(seconds=1.5, message="external call timed out", exception=ExternalCallTimedOut)
async def call_external_service() -> str:
    ...
```
