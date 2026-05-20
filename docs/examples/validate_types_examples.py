"""Executable examples for @validate_types documentation."""

import asyncio

from pydecorators import validate_types


def argument_validation_example() -> str:
    """Validate simple annotated arguments at call time."""

    @validate_types()
    def greet(name: str, excited: bool = False) -> str:
        return f"hello {name}{'!' if excited else ''}"

    return greet("Ada", excited=True)


def argument_error_example() -> str:
    """Handle a simple argument type mismatch."""

    @validate_types()
    def double(value: int) -> int:
        return value * 2

    try:
        double("not an int")  # type: ignore[arg-type]
    except TypeError as exc:
        return str(exc)
    return "accepted"


def return_validation_example() -> str:
    """Opt into validating annotated return values."""

    @validate_types(validate_return=True)
    def load_status() -> str:
        return "ready"

    return load_status()


async def async_validation_example() -> str:
    """Use the same validation behavior with async functions."""

    @validate_types(validate_return=True)
    async def fetch_name(user_id: str | None) -> str:
        await asyncio.sleep(0)
        return f"user:{user_id or 'anonymous'}"

    return await fetch_name(None)
