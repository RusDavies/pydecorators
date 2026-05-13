# `@measure_time`

`@measure_time` records how long a sync or async function takes and emits structured timing data to callbacks, loggers, or simple metrics hooks.

```python
from useful_decorators import measure_time


@measure_time()
def rebuild_index() -> None:
    ...
```

With no callback, logger, or metrics hook, the decorator only measures internally and has no visible output. Configure at least one sink when timing data should be collected.

## Parameters

- `callback`: optional callable receiving a `TimingInfo` object.
- `logger`: optional `logging.Logger` that receives a duration log line.
- `level`: integer logging level for logger output. Defaults to `logging.INFO`.
- `metrics_hook`: optional callable receiving `(function_name, duration, success)`.
- `clock`: injectable clock for deterministic tests.

Invalid configuration raises `ConfigurationError` at decoration time.

Logger records include `useful_decorators_function`, `useful_decorators_duration_seconds`, and `useful_decorators_success` in `logging`'s `extra` data so log pipelines can aggregate timing data without parsing the message text.

Durations use Python's monotonic clock by default. This makes elapsed-time measurement resilient to wall-clock changes such as NTP adjustments, daylight saving transitions, or virtual-machine clock jumps. Inject `clock=` only for deterministic tests or specialized runtime integrations; production clocks should be monotonic-style functions that return increasing seconds.

## `TimingInfo`

`TimingInfo` is an immutable dataclass with:

- `function`: wrapped function `__qualname__`.
- `duration`: elapsed seconds.
- `success`: whether the wrapped function returned normally.
- `exception`: the exception object when the wrapped function failed, otherwise `None`.

The decorator records timings for both success and failure paths, then re-raises exceptions unchanged.

## Examples

Callback collection:

```python
from useful_decorators import TimingInfo, measure_time


timings: list[TimingInfo] = []


@measure_time(callback=timings.append)
def load_report() -> str:
    return "ready"
```

Logger output:

```python
import logging

from useful_decorators import measure_time

logger = logging.getLogger("timings")


@measure_time(logger=logger)
def rebuild_cache() -> None:
    ...
```

Metrics hook:

```python
@measure_time(metrics_hook=lambda name, duration, success: metrics.observe(name, duration))
def handle_job() -> None:
    ...
```


## Executable examples

Copy-pasteable examples live in `docs/examples/measure_time_examples.py` and are
covered by `tests/test_docs_examples.py`. They demonstrate callback collection,
metrics hooks, and async timing with an injectable clock for deterministic output.
