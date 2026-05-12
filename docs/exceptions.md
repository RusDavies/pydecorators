# Public Exceptions

This page summarizes the public exception hierarchy exposed by `useful_decorators`.

Use the most specific exception when you can recover from a known condition. Catch `UsefulDecoratorsError` when you want to handle package-specific failures without catching unrelated Python exceptions.

## Exception hierarchy

| Exception | Inherits from | Raised when |
| --- | --- | --- |
| `UsefulDecoratorsError` | `Exception` | Base class for package-specific exceptions. |
| `ConfigurationError` | `ValueError`, `UsefulDecoratorsError` | A decorator or backend receives invalid configuration. |
| `CacheKeyError` | `TypeError`, `UsefulDecoratorsError` | `@cache_result` cannot build a hashable cache key. |
| `CacheSerializationError` | `UsefulDecoratorsError` | Cache payload serialization or deserialization fails. |
| `CacheBackendClosedError` | `UsefulDecoratorsError` | A closeable cache backend such as `DiskCacheBackend` is used after `close()`. |
| `RateLimitExceeded` | `UsefulDecoratorsError` | A future rate-limited call exceeds its configured allowance. |
| `FunctionTimedOut` | `TimeoutError`, `UsefulDecoratorsError` | A future timeout-decorated function exceeds its configured timeout. |

## Examples

Executable examples live in `docs/examples/public_exception_examples.py` and are covered by `tests/test_docs_examples.py`.

### `ConfigurationError`

```python
from useful_decorators import ConfigurationError, cache_result

try:
    cache_result(namespace="   ")
except ConfigurationError:
    ...
```

### `CacheKeyError`

```python
from useful_decorators import CacheKeyError, cache_result

@cache_result()
def identity(value: list[int]) -> list[int]:
    return value

try:
    identity([1, 2, 3])
except CacheKeyError:
    ...
```

### `CacheSerializationError`

```python
from useful_decorators import CacheSerializationError, JsonCacheSerializer, PickleCacheSerializer

try:
    PickleCacheSerializer().dumps(lambda value: value)
except CacheSerializationError:
    ...

try:
    JsonCacheSerializer().dumps({"not_json": object()})
except CacheSerializationError:
    ...
```

### `CacheBackendClosedError`

```python
from useful_decorators import CacheBackendClosedError, DiskCacheBackend

backend = DiskCacheBackend(".cache/example.sqlite3")
backend.close()

try:
    backend.info()
except CacheBackendClosedError:
    ...
```
