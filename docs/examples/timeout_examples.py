"""Executable examples for @timeout documentation."""

import asyncio

from pydecorators import FunctionTimedOut, timeout


async def successful_timeout_example() -> str:
    """Complete before the timeout deadline."""

    @timeout(seconds=1)
    async def quick_call() -> str:
        await asyncio.sleep(0)
        return "finished"

    return await quick_call()


async def timeout_failure_example() -> str:
    """Handle a coroutine that exceeds its timeout deadline."""

    @timeout(seconds=0.01)
    async def slow_call() -> str:
        await asyncio.sleep(1)
        return "late"

    try:
        await slow_call()
    except FunctionTimedOut:
        return "timed out"
    return "finished"


async def custom_timeout_exception_example() -> str:
    """Use a custom timeout exception that accepts a message string."""

    class ExternalServiceTimedOut(Exception):
        pass

    @timeout(seconds=0.01, message="vendor call timed out", exception=ExternalServiceTimedOut)
    async def call_vendor() -> str:
        await asyncio.sleep(1)
        return "late"

    try:
        await call_vendor()
    except ExternalServiceTimedOut as exc:
        return str(exc)
    return "finished"
