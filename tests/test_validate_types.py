import asyncio
from typing import Annotated, Any, Literal, cast

import pytest

from useful_decorators import ConfigurationError, ValidationError, validate_types


def test_validate_types_accepts_basic_builtin_types() -> None:
    @validate_types()
    def greet(name: str, excited: bool = False) -> str:
        return f"hello {name}{'!' if excited else ''}"

    assert greet("Ada", excited=True) == "hello Ada!"


def test_validate_types_rejects_wrong_argument_type_with_clear_message() -> None:
    @validate_types()
    def double(value: int) -> int:
        return value * 2

    with pytest.raises(ValidationError, match="argument 'value' expected int, got str"):
        double("nope")  # type: ignore[arg-type]


def test_validate_types_supports_optional_and_union_types() -> None:
    @validate_types()
    def normalize(value: str | None, fallback: int | str) -> str:
        return str(value if value is not None else fallback)

    assert normalize(None, 3) == "3"
    assert normalize("x", "fallback") == "x"
    with pytest.raises(ValidationError, match="argument 'fallback' expected"):
        normalize(None, object())  # type: ignore[arg-type]


def test_validate_types_supports_common_container_origins_without_deep_checks() -> None:
    @validate_types()
    def count(values: list[int]) -> int:
        return len(values)

    assert count([1, 2, 3]) == 3
    assert count(["not checked deeply"]) == 1  # type: ignore[list-item]
    with pytest.raises(ValidationError, match="argument 'values' expected list"):
        count((1, 2, 3))  # type: ignore[arg-type]


def test_validate_types_can_validate_container_contents_when_deep_enabled() -> None:
    @validate_types(deep=True, validate_return=True)
    def normalize(values: list[int], metadata: dict[str, tuple[str, ...]]) -> set[str]:
        return {str(value) for value in values} | set(metadata["tags"])

    assert normalize([1, 2], {"tags": ("a", "b")}) == {"1", "2", "a", "b"}
    with pytest.raises(ValidationError, match="argument 'values' expected list"):
        normalize([1, "bad"], {"tags": ("a",)})  # type: ignore[list-item]
    with pytest.raises(ValidationError, match="argument 'metadata' expected dict"):
        normalize([1], {1: ("a",)})  # type: ignore[dict-item]


def test_validate_types_supports_literal_and_annotated() -> None:
    @validate_types()
    def configure(mode: Literal["fast", "safe"], retries: Annotated[int, "non-negative"]) -> str:
        return f"{mode}:{retries}"

    assert configure("fast", 3) == "fast:3"
    expected_message = r"argument 'mode' expected Literal\['fast', 'safe'\]"
    with pytest.raises(ValidationError, match=expected_message):
        configure("slow", 3)  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="argument 'retries' expected int, got str"):
        configure("safe", "many")  # type: ignore[arg-type]


def test_validate_types_can_validate_return_value() -> None:
    @validate_types(validate_return=True)
    def broken() -> int:
        return "not an int"  # type: ignore[return-value]

    with pytest.raises(ValidationError, match="return value expected int, got str"):
        broken()


def test_validate_types_skips_return_validation_by_default() -> None:
    @validate_types()
    def broken() -> int:
        return "not an int"  # type: ignore[return-value]

    result = cast(object, broken())
    assert result == "not an int"


@pytest.mark.asyncio
async def test_validate_types_supports_async_functions() -> None:
    @validate_types(validate_return=True)
    async def add_one(value: int | None) -> int:
        await asyncio.sleep(0)
        return 1 if value is None else value + 1

    assert await add_one(None) == 1
    with pytest.raises(ValidationError, match="argument 'value' expected"):
        await add_one("bad")  # type: ignore[arg-type]


def test_validate_types_preserves_metadata() -> None:
    @validate_types()
    def documented(value: int) -> int:
        """Original docs."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Original docs."
    assert documented.__wrapped__ is not None  # type: ignore[attr-defined]


def test_validate_types_validates_configuration() -> None:
    with pytest.raises(ConfigurationError, match="validate_return must be a boolean"):
        validate_types(validate_return="yes")  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError, match="deep must be a boolean"):
        validate_types(deep="yes")  # type: ignore[arg-type]


def test_validate_types_ignores_unannotated_arguments_and_any() -> None:
    @validate_types(validate_return=True)
    def passthrough(value, metadata: Any) -> Any:  # type: ignore[no-untyped-def]
        return metadata

    assert passthrough(object(), metadata={"ok": True}) == {"ok": True}
