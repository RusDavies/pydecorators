"""Executable optional observability integration examples."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from useful_decorators import TimingInfo, log_calls, measure_time, retry


@dataclass
class _FakeSpan:
    """Tiny OpenTelemetry-span stand-in for dependency-free docs tests."""

    name: str
    attributes: dict[str, object] = field(default_factory=dict)
    exceptions: list[str] = field(default_factory=list)

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value

    def record_exception(self, exception: BaseException) -> None:
        self.exceptions.append(type(exception).__name__)


@dataclass
class _FakeTracer:
    """Tiny tracer stand-in exposing the shape used by the example callback."""

    spans: list[_FakeSpan] = field(default_factory=list)

    def start_span(self, name: str) -> _FakeSpan:
        span = _FakeSpan(name)
        self.spans.append(span)
        return span


@dataclass
class _FakeHistogram:
    """Tiny Prometheus-histogram stand-in for observe-style callbacks."""

    observations: list[tuple[float, dict[str, str]]] = field(default_factory=list)

    def labels(self, **labels: str) -> "_FakeHistogram":
        self._active_labels = labels
        return self

    def observe(self, value: float) -> None:
        self.observations.append((value, getattr(self, "_active_labels", {})))


@dataclass
class _FakeStructLogger:
    """Tiny structlog-style logger stand-in."""

    events: list[tuple[str, dict[str, object]]] = field(default_factory=list)

    def bind(self, **context: object) -> "_FakeStructLogger":
        logger = _FakeStructLogger(self.events)
        logger.events.append(("bind", context))
        return logger

    def info(self, event: str, **fields: object) -> None:
        self.events.append((event, fields))

    def warning(self, event: str, **fields: object) -> None:
        self.events.append((event, fields))


def opentelemetry_measure_time_example() -> dict[str, object]:
    """Bridge ``measure_time(callback=...)`` into an OpenTelemetry-style span."""

    tracer = _FakeTracer()

    def emit_timing(info: TimingInfo) -> None:
        span = tracer.start_span(f"decorator.{info.function}")
        span.set_attribute("decorator.duration_ms", round(info.duration * 1000, 3))
        span.set_attribute("decorator.success", info.success)
        if info.exception is not None:
            span.record_exception(info.exception)

    @measure_time(callback=emit_timing, clock=_sequence_clock([10.0, 10.125]))
    def load_profile() -> str:
        return "profile"

    result = load_profile()
    span = tracer.spans[0]
    return {"result": result, "span": span.name, "attributes": span.attributes}


def prometheus_measure_time_example() -> list[tuple[float, dict[str, str]]]:
    """Bridge ``measure_time(callback=...)`` into a Prometheus-style histogram."""

    histogram = _FakeHistogram()

    def observe_timing(info: TimingInfo) -> None:
        histogram.labels(function=info.function, success=str(info.success).lower()).observe(
            info.duration
        )

    @measure_time(callback=observe_timing, clock=_sequence_clock([20.0, 20.25]))
    def refresh_index() -> str:
        return "refreshed"

    refresh_index()
    return histogram.observations


def structlog_log_calls_example() -> list[tuple[str, dict[str, object]]]:
    """Use ``log_calls`` with a small logging.Logger adapter around structlog."""

    structured = _FakeStructLogger()

    class StructlogAdapter:
        def log(self, _level: int, message: str, *args: object, **kwargs: Any) -> None:
            event = message % args if args else message
            extra = kwargs.get("extra")
            fields = extra if isinstance(extra, dict) else {}
            structured.bind(component="decorators").info(event, **fields)

    @log_calls(logger=StructlogAdapter())  # type: ignore[arg-type]
    def list_jobs() -> list[str]:
        return ["build", "publish"]

    list_jobs()
    return structured.events


def retry_attempt_logging_example() -> list[tuple[str, dict[str, object]]]:
    """Use retry hooks to emit structured attempt events."""

    logger = _FakeStructLogger()
    calls = 0

    def before_attempt(attempt: int) -> None:
        logger.info("retry.before_attempt", attempt=attempt)

    def after_attempt(attempt: int, exception: BaseException | None) -> None:
        logger.info(
            "retry.after_attempt",
            attempt=attempt,
            exception=type(exception).__name__ if exception else None,
        )

    @retry(
        attempts=2,
        delay=0,
        exceptions=(ConnectionError,),
        before_attempt=before_attempt,
        after_attempt=after_attempt,
    )
    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ConnectionError("try again")
        return "ok"

    flaky()
    return logger.events


def _sequence_clock(values: list[float]) -> Callable[[], float]:
    iterator = iter(values)
    return lambda: next(iterator)
