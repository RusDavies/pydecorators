# Public Exceptions

This page summarizes the public exception hierarchy exposed by `useful_decorators`.

Use the most specific exception when you can recover from a known condition. Catch `UsefulDecoratorsError` when you want to handle package-specific failures without catching unrelated Python exceptions.

## Exception hierarchy

| Exception | Inherits from | Raised when |
| --- | --- | --- |
| `UsefulDecoratorsError` | `Exception` | Base class for package-specific exceptions. |
| `ConfigurationError` | `ValueError`, `UsefulDecoratorsError` | A decorator or backend receives invalid configuration. |
| `CircuitBreakerOpen` | `UsefulDecoratorsError` | A circuit-breaker-protected call is rejected because the circuit is open. |
| `CacheKeyError` | `TypeError`, `UsefulDecoratorsError` | `@cache_result` cannot build a hashable cache key. |
| `ValidationError` | `TypeError`, `UsefulDecoratorsError` | `@validate_types` finds an argument or return value mismatch. |
| `CacheSerializationError` | `UsefulDecoratorsError` | Cache payload serialization or deserialization fails. |
| `CacheBackendClosedError` | `UsefulDecoratorsError` | A closeable cache backend such as `DiskCacheBackend` is used after `close()`. |
| `UnsupportedCacheSchemaVersionError` | `UsefulDecoratorsError` | A persistent cache file uses a newer schema version than this package supports. |
| `RateLimitExceeded` | `UsefulDecoratorsError` | A future rate-limited call exceeds its configured allowance. |
| `FunctionTimedOut` | `TimeoutError`, `UsefulDecoratorsError` | A future timeout-decorated function exceeds its configured timeout. |
| `EnvRequirementError` | `RuntimeError` | `@require_env` finds a missing or invalid required environment variable. |

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

### `CircuitBreakerOpen`

```python
from useful_decorators import CircuitBreakerOpen, circuit_breaker

@circuit_breaker(failure_threshold=1, reset_timeout=10)
def call_service() -> None:
    raise RuntimeError("down")

try:
    call_service()
    call_service()
except CircuitBreakerOpen:
    ...
except RuntimeError:
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

### `UnsupportedCacheSchemaVersionError`

```python
from useful_decorators import DiskCacheBackend, UnsupportedCacheSchemaVersionError

try:
    DiskCacheBackend(".cache/example.sqlite3")
except UnsupportedCacheSchemaVersionError:
    # Upgrade useful-decorators, choose a compatible cache file, or rebuild the cache.
    ...
```

### `ValidationError`

```python
from useful_decorators import ValidationError, validate_types

@validate_types()
def double(value: int) -> int:
    return value * 2

try:
    double("bad")
except ValidationError:
    ...
```

### `RateLimitExceeded`

```python
from useful_decorators import RateLimitExceeded, rate_limit

@rate_limit(calls=1, period=60)
def limited() -> str:
    return "ok"

try:
    limited()
    limited()
except RateLimitExceeded as exc:
    retry_after = exc.retry_after
```

### `FunctionTimedOut`

```python
from useful_decorators import FunctionTimedOut, timeout

@timeout(seconds=0.5)
async def slow_call() -> str:
    ...

try:
    await slow_call()
except FunctionTimedOut:
    ...
```

### `EnvRequirementError`

```python
from useful_decorators import EnvRequirementError, require_env

@require_env("API_TOKEN", environ={})
def call_service() -> None:
    ...

try:
    call_service()
except EnvRequirementError:
    ...
```
