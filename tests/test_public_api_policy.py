import re
from pathlib import Path

import useful_decorators


def documented_public_api_names() -> set[str]:
    text = Path("docs/PUBLIC_API.md").read_text()
    section = text.split("## Internal API", maxsplit=1)[0]
    return set(re.findall(r"^- `([^`]+)`", section, flags=re.MULTILINE))


def test_documented_public_api_matches_all_exports() -> None:
    assert documented_public_api_names() == set(useful_decorators.__all__)


def test_ci_matrix_includes_minimum_supported_python_version() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text()
    pyproject = Path("pyproject.toml").read_text()

    assert 'requires-python = ">=3.11"' in pyproject
    assert '"3.11"' in workflow
