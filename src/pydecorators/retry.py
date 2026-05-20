"""Retry decorator for transient failures."""

from __future__ import annotations

import inspect
import random
from collections.abc import Callable
from typing import Any, cast

from pydecorators._core import async_sleep, is_async_callable, mirror_metadata, sync_sleep
from pydecorators._typing import P, R
from pydecorators.exceptions import ConfigurationError

RetryPredicate = Callable[[BaseException], bool]
BeforeAttemptHook = Callable[[int], object]
AfterAttemptHook = Callable[[int, BaseException | None], object]


def retry(
    *,
    attempts: int,
    delay: float = 0,
    backoff: float = 1,
    max_delay: float | None = None,
    jitter: float = 0,
    exceptions: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    retry_if: RetryPredicate | None = None,
    before_attempt: BeforeAttemptHook | None = None,
    after_attempt: AfterAttemptHook | None = None,
    sleep: Callable[[float], object] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a sync or async callable after configured exceptions."""

    _validate_retry_config(
        attempts=attempts,
        delay=delay,
        backoff=backoff,
        max_delay=max_delay,
        jitter=jitter,
        exceptions=exceptions,
        retry_if=retry_if,
        before_attempt=before_attempt,
        after_attempt=after_attempt,
    )
    exception_types = _normalize_exceptions(exceptions)

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        if is_async_callable(func):
            async_func = cast(Callable[P, Any], func)
            async_sleep_func = cast(Callable[[float], Any], sleep or async_sleep)

            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
                current_delay = delay
                for attempt_number in range(1, attempts + 1):
                    await _call_before_async(before_attempt, attempt_number)
                    try:
                        result = async_func(*args, **kwargs)
                        if hasattr(result, "__await__"):
                            result = await result
                        await _call_after_async(after_attempt, attempt_number, None)
                        return result
                    except exception_types as exc:
                        await _call_after_async(after_attempt, attempt_number, exc)
                        if not _should_retry(
                            exc,
                            attempt_number=attempt_number,
                            attempts=attempts,
                            retry_if=retry_if,
                        ):
                            raise
                        await async_sleep_func(_delay_with_jitter(current_delay, jitter))
                        current_delay = _next_delay(current_delay, backoff, max_delay)

                raise AssertionError("retry loop exhausted without returning or raising")

            return mirror_metadata(cast(Callable[P, R], async_wrapper), cast(Callable[P, R], func))

        sync_sleep_func = sleep or sync_sleep

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            current_delay = delay
            for attempt_number in range(1, attempts + 1):
                _call_before(before_attempt, attempt_number)
                try:
                    result = func(*args, **kwargs)
                    _call_after(after_attempt, attempt_number, None)
                    return result
                except exception_types as exc:
                    _call_after(after_attempt, attempt_number, exc)
                    if not _should_retry(
                        exc,
                        attempt_number=attempt_number,
                        attempts=attempts,
                        retry_if=retry_if,
                    ):
                        raise
                    sync_sleep_func(_delay_with_jitter(current_delay, jitter))
                    current_delay = _next_delay(current_delay, backoff, max_delay)

            raise AssertionError("retry loop exhausted without returning or raising")

        return mirror_metadata(wrapper, func)

    return decorate


def _validate_retry_config(
    *,
    attempts: int,
    delay: float,
    backoff: float,
    max_delay: float | None,
    jitter: float,
    exceptions: type[BaseException] | tuple[type[BaseException], ...],
    retry_if: RetryPredicate | None,
    before_attempt: BeforeAttemptHook | None,
    after_attempt: AfterAttemptHook | None,
) -> None:
    if attempts <= 0:
        raise ConfigurationError("attempts must be greater than zero")
    if delay < 0:
        raise ConfigurationError("delay must be zero or greater")
    if backoff < 1:
        raise ConfigurationError("backoff must be greater than or equal to 1")
    if max_delay is not None and max_delay < 0:
        raise ConfigurationError("max_delay must be zero or greater when provided")
    if jitter < 0:
        raise ConfigurationError("jitter must be zero or greater")
    _normalize_exceptions(exceptions)
    if retry_if is not None and not callable(retry_if):
        raise ConfigurationError("retry_if must be callable when provided")
    if before_attempt is not None and not callable(before_attempt):
        raise ConfigurationError("before_attempt must be callable when provided")
    if after_attempt is not None and not callable(after_attempt):
        raise ConfigurationError("after_attempt must be callable when provided")


def _normalize_exceptions(
    exceptions: type[BaseException] | tuple[type[BaseException], ...],
) -> tuple[type[BaseException], ...]:
    normalized = exceptions if isinstance(exceptions, tuple) else (exceptions,)
    if not normalized:
        raise ConfigurationError("exceptions must include at least one exception type")
    if not all(isinstance(item, type) and issubclass(item, BaseException) for item in normalized):
        raise ConfigurationError("exceptions must be exception types")
    return normalized


def _should_retry(
    exc: BaseException,
    *,
    attempt_number: int,
    attempts: int,
    retry_if: RetryPredicate | None,
) -> bool:
    if attempt_number >= attempts:
        return False
    if retry_if is None:
        return True
    return retry_if(exc)


def _delay_with_jitter(delay: float, jitter: float) -> float:
    if jitter == 0:
        return delay
    return delay + random.uniform(0, jitter)


def _next_delay(delay: float, backoff: float, max_delay: float | None) -> float:
    next_delay = delay * backoff
    if max_delay is not None:
        return min(next_delay, max_delay)
    return next_delay


def _call_before(hook: BeforeAttemptHook | None, attempt_number: int) -> None:
    if hook is not None:
        hook(attempt_number)


def _call_after(
    hook: AfterAttemptHook | None,
    attempt_number: int,
    exc: BaseException | None,
) -> None:
    if hook is not None:
        hook(attempt_number, exc)


async def _call_before_async(hook: BeforeAttemptHook | None, attempt_number: int) -> None:
    if hook is None:
        return
    result = hook(attempt_number)
    if inspect.isawaitable(result):
        await result


async def _call_after_async(
    hook: AfterAttemptHook | None,
    attempt_number: int,
    exc: BaseException | None,
) -> None:
    if hook is None:
        return
    result = hook(attempt_number, exc)
    if inspect.isawaitable(result):
        await result
