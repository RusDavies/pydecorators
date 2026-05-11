import inspect
import re
from pathlib import Path

import useful_decorators


def documented_public_api_names() -> set[str]:
    text = Path("docs/PUBLIC_API.md").read_text()
    section = text.split("## Internal API", maxsplit=1)[0]
    return set(re.findall(r"^- `([^`]+)`", section, flags=re.MULTILINE))


def public_api_note_for(name: str) -> str:
    public_api = Path("docs/PUBLIC_API.md").read_text()
    match = re.search(
        rf"^### `{re.escape(name)}`\n(?P<body>.*?)(?=^### `|\Z)",
        public_api,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def test_documented_public_api_matches_all_exports() -> None:
    assert documented_public_api_names() == set(useful_decorators.__all__)


def test_ci_matrix_includes_minimum_supported_python_version() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text()
    pyproject = Path("pyproject.toml").read_text()

    assert 'requires-python = ">=3.11"' in pyproject
    assert '"3.11"' in workflow


def test_public_exceptions_are_documented_in_public_api_notes() -> None:
    public_api = Path("docs/PUBLIC_API.md").read_text()
    public_exception_names = {
        name
        for name in useful_decorators.__all__
        if inspect.isclass(getattr(useful_decorators, name))
        and issubclass(getattr(useful_decorators, name), BaseException)
    }

    assert public_exception_names
    for name in public_exception_names:
        assert f"### `{name}`" in public_api


def test_public_exception_inheritance_matches_documentation() -> None:
    inheritance_phrases: dict[type[BaseException], str] = {
        useful_decorators.UsefulDecoratorsError: "base class for package-specific exceptions",
        useful_decorators.ConfigurationError: "ValueError",
        useful_decorators.RateLimitExceeded: "UsefulDecoratorsError",
        useful_decorators.FunctionTimedOut: "TimeoutError",
        useful_decorators.CacheKeyError: "TypeError",
        useful_decorators.CacheSerializationError: "UsefulDecoratorsError",
        useful_decorators.CacheBackendClosedError: "UsefulDecoratorsError",
    }

    for exception_type, expected_phrase in inheritance_phrases.items():
        note = public_api_note_for(exception_type.__name__)
        assert expected_phrase in note


def test_public_exceptions_reference_covers_public_exceptions() -> None:
    exceptions_reference = Path("docs/exceptions.md").read_text()
    public_exception_names = {
        name
        for name in useful_decorators.__all__
        if inspect.isclass(getattr(useful_decorators, name))
        and issubclass(getattr(useful_decorators, name), BaseException)
    }

    assert "docs/examples/public_exception_examples.py" in exceptions_reference
    for name in public_exception_names:
        assert f"`{name}`" in exceptions_reference
