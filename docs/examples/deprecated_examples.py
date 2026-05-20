"""Executable examples for the deprecated decorator documentation."""

from __future__ import annotations

from pydecorators import deprecated


@deprecated
def old_bare_function(left: int, right: int) -> int:
    """Add two numbers using bare deprecation syntax."""

    return left + right


@deprecated("Use add instead.", replacement="add", version="0.1.0")
def old_configured_function(left: int, right: int) -> int:
    """Add two numbers using configured deprecation syntax."""

    return left + right


@deprecated(replacement="fetch_new")
async def old_async_function() -> str:
    """Return async example data."""

    return "data"


class Client:
    """Example client with a deprecated method."""

    @deprecated(replacement="Client.fetch_new")
    def fetch_old(self) -> str:
        """Return old client data."""

        return "old"
