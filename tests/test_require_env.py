import asyncio
from collections.abc import MutableMapping
from typing import Any

import pytest

from useful_decorators import ConfigurationError, EnvRequirementError, require_env


def test_require_env_allows_call_when_variable_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_TOKEN", "secret")

    @require_env("API_TOKEN")
    def call_service() -> str:
        return "ok"

    assert call_service() == "ok"


def test_require_env_raises_when_variable_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_TOKEN", raising=False)

    @require_env("API_TOKEN")
    def call_service() -> str:
        return "ok"

    with pytest.raises(EnvRequirementError, match="'API_TOKEN' is required"):
        call_service()


def test_require_env_supports_multiple_names_and_validators() -> None:
    environ = {"API_TOKEN": "abc", "REGION": "ca"}

    @require_env(
        "API_TOKEN",
        "REGION",
        validators={"REGION": lambda value: value in {"ca", "us"}},
        environ=environ,
    )
    def call_service() -> str:
        return "ok"

    assert call_service() == "ok"


def test_require_env_raises_when_validator_returns_false() -> None:
    environ = {"REGION": "moon"}

    @require_env(
        "REGION",
        validators={"REGION": lambda value: value in {"ca", "us"}},
        environ=environ,
    )
    def call_service() -> str:
        return "ok"

    with pytest.raises(EnvRequirementError, match="'REGION' failed validation"):
        call_service()


def test_require_env_checks_at_call_time() -> None:
    environ: MutableMapping[str, str] = {}

    @require_env("API_TOKEN", environ=environ)
    def call_service() -> str:
        return "ok"

    with pytest.raises(EnvRequirementError):
        call_service()
    environ["API_TOKEN"] = "later"
    assert call_service() == "ok"


@pytest.mark.asyncio
async def test_require_env_supports_async_functions() -> None:
    environ = {"API_TOKEN": "secret"}

    @require_env("API_TOKEN", environ=environ)
    async def call_service() -> str:
        await asyncio.sleep(0)
        return "ok"

    assert await call_service() == "ok"


def test_require_env_preserves_metadata() -> None:
    @require_env("API_TOKEN", environ={"API_TOKEN": "secret"})
    def documented() -> str:
        """Original docs."""
        return "ok"

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("args", "kwargs", "message"),
    [
        ((), {}, "needs at least one variable"),
        (("",), {}, "names must be non-empty strings"),
        (("API_TOKEN",), {"validators": {"OTHER": lambda value: True}}, "unknown variable"),
        (("API_TOKEN",), {"validators": {"API_TOKEN": object()}}, "must be callable"),
        (("API_TOKEN",), {"environ": object()}, "environ must be a mapping"),
    ],
)
def test_require_env_validates_configuration(
    args: tuple[Any, ...], kwargs: dict[str, Any], message: str
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        require_env(*args, **kwargs)
