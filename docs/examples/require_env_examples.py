"""Executable examples for @require_env documentation."""

import asyncio

from pydecorators import EnvRequirementError, require_env


def required_variables_example() -> str:
    """Run only when all required variables are present."""

    env = {"API_TOKEN": "secret", "REGION": "ca"}

    @require_env("API_TOKEN", "REGION", environ=env)
    def call_service() -> str:
        return "called"

    return call_service()


def missing_variable_example() -> str:
    """Handle a missing required variable."""

    @require_env("API_TOKEN", environ={})
    def call_service() -> str:
        return "called"

    try:
        call_service()
    except EnvRequirementError as exc:
        return str(exc)
    return "called"


def validator_example() -> str:
    """Reject variables that fail custom validation."""

    env = {"REGION": "moon"}

    @require_env("REGION", validators={"REGION": lambda value: value in {"ca", "us"}}, environ=env)
    def call_regional_service() -> str:
        return "called"

    try:
        call_regional_service()
    except EnvRequirementError as exc:
        return str(exc)
    return "called"


async def async_require_env_example() -> str:
    """Use the same call-time checks with async functions."""

    env = {"API_TOKEN": "secret"}

    @require_env("API_TOKEN", environ=env)
    async def refresh_user() -> str:
        await asyncio.sleep(0)
        return "refreshed"

    return await refresh_user()
