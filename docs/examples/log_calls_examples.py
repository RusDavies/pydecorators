"""Executable examples for @log_calls documentation."""

import asyncio
import logging

from pydecorators import log_calls


class _ListHandler(logging.Handler):
    """Capture formatted log records for documentation examples."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _example_logger(name: str) -> tuple[logging.Logger, _ListHandler]:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = _ListHandler()
    logger.addHandler(handler)
    return logger, handler


def redacted_arguments_example() -> list[str]:
    """Log keyword arguments while redacting selected names."""

    logger, handler = _example_logger("docs.log_calls.redacted")

    @log_calls(logger=logger, include_args=True, redact_args={"api_key"})
    def fetch_user(*, user_id: str, api_key: str) -> str:
        return f"user:{user_id}"

    fetch_user(user_id="123", api_key="secret")
    return handler.messages


def summarized_result_example() -> list[str]:
    """Summarize a result before writing it to logs."""

    logger, handler = _example_logger("docs.log_calls.summary")

    @log_calls(
        logger=logger,
        include_result=True,
        summarize_result=lambda result: {"count": len(result)},
    )
    def list_jobs() -> list[str]:
        return ["build", "test", "publish"]

    list_jobs()
    return handler.messages


async def async_logging_example() -> list[str]:
    """Use the same logging behavior with async functions."""

    logger, handler = _example_logger("docs.log_calls.async")

    @log_calls(logger=logger)
    async def refresh_user(user_id: str) -> str:
        await asyncio.sleep(0)
        return f"refreshed:{user_id}"

    await refresh_user("123")
    return handler.messages
