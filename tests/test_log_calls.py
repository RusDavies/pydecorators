import asyncio
import logging
from typing import Any, cast

import pytest

from useful_decorators import ConfigurationError, log_calls


class MutableClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        current = self.now
        self.now += 0.25
        return current


def messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records]


def extra(record: logging.LogRecord, name: str) -> object:
    return record.__dict__[name]


def test_log_calls_logs_sync_start_finish_and_duration(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.log_calls.sync")
    clock = MutableClock()

    @log_calls(logger=logger, clock=clock)
    def add(left: int, right: int) -> int:
        return left + right

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert add(1, 2) == 3

    logged = messages(caplog)
    assert logged[0].endswith("add started")
    assert logged[1].endswith("add finished in 0.25 seconds")
    assert str(extra(caplog.records[0], "useful_decorators_function")).endswith("add")
    assert extra(caplog.records[0], "useful_decorators_event") == "started"
    assert extra(caplog.records[1], "useful_decorators_event") == "finished"
    assert extra(caplog.records[1], "useful_decorators_duration_seconds") == 0.25
    assert extra(caplog.records[1], "useful_decorators_success") is True


def test_log_calls_can_include_redacted_keyword_arguments(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.log_calls.args")

    @log_calls(logger=logger, include_args=True, redact_args={"password"})
    def authenticate(*, username: str, password: str) -> bool:
        return username == "ada" and password == "secret"

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert authenticate(username="ada", password="secret") is True

    joined = "\n".join(messages(caplog))
    assert "'username': 'ada'" in joined
    assert "'password': '<redacted>'" in joined
    assert "secret" not in joined


def test_log_calls_can_redact_positional_arguments_by_parameter_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("tests.log_calls.positional_args")

    @log_calls(logger=logger, include_args=True, redact_args={"password"})
    def authenticate(username: str, password: str) -> bool:
        return username == "ada" and password == "secret"

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert authenticate("ada", "secret") is True

    joined = "\n".join(messages(caplog))
    assert "args=('ada', '<redacted>')" in joined
    assert "secret" not in joined


def test_log_calls_can_include_summarized_return_value(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.log_calls.result")

    @log_calls(
        logger=logger,
        include_result=True,
        summarize_result=lambda result: {"items": len(cast(list[int], result))},
    )
    def load_items() -> list[int]:
        return [1, 2, 3]

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert load_items() == [1, 2, 3]

    assert "result={'items': 3}" in "\n".join(messages(caplog))


def test_log_calls_logs_exceptions_without_swallowing_them(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("tests.log_calls.exception")

    @log_calls(logger=logger)
    def broken() -> None:
        raise ValueError("boom")

    with caplog.at_level(logging.INFO, logger=logger.name), pytest.raises(ValueError, match="boom"):
        broken()

    joined = "\n".join(messages(caplog))
    assert "broken started" in joined
    assert "broken failed after" in joined
    assert extra(caplog.records[-1], "useful_decorators_event") == "failed"
    assert extra(caplog.records[-1], "useful_decorators_success") is False


@pytest.mark.asyncio
async def test_log_calls_supports_async_functions(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.log_calls.async")

    @log_calls(logger=logger)
    async def async_add(left: int, right: int) -> int:
        await asyncio.sleep(0)
        return left + right

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert await async_add(1, 2) == 3

    joined = "\n".join(messages(caplog))
    assert "async_add started" in joined
    assert "async_add finished" in joined


@pytest.mark.asyncio
async def test_log_calls_awaits_async_result_summarizer_for_async_functions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("tests.log_calls.async_summarizer")

    async def summarize(result: object) -> object:
        await asyncio.sleep(0)
        return {"length": len(cast(list[int], result))}

    @log_calls(logger=logger, include_result=True, summarize_result=summarize)
    async def load_items() -> list[int]:
        return [1, 2, 3]

    with caplog.at_level(logging.INFO, logger=logger.name):
        assert await load_items() == [1, 2, 3]

    assert "result={'length': 3}" in "\n".join(messages(caplog))


def test_log_calls_preserves_metadata() -> None:
    @log_calls()
    def documented(value: int) -> int:
        """Original docs."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"level": "info"}, "level must be an integer"),
        ({"redact_args": ["password", 123]}, "redact_args must contain only"),
        ({"summarize_result": object()}, "summarize_result must be callable"),
        ({"clock": object()}, "clock must be callable"),
    ],
)
def test_log_calls_validates_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        log_calls(**kwargs)
