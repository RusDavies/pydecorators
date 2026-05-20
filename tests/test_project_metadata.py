import tomllib
from pathlib import Path
from typing import Any, cast


def project_metadata() -> dict[str, Any]:
    return cast(dict[str, Any], tomllib.loads(Path("pyproject.toml").read_text())["project"])


def test_project_metadata_is_release_ready_except_name_decision() -> None:
    project = project_metadata()

    assert project["name"] == "blakemere-wraptools"
    assert project["description"]
    assert project["readme"] == "README.md"
    assert project["requires-python"] == ">=3.11"
    assert project["license"] == "MIT"
    assert project["authors"]
    assert project["keywords"]
    assert project["classifiers"]


def test_project_urls_are_documented() -> None:
    urls = cast(dict[str, str], project_metadata()["urls"])

    assert urls["Homepage"].startswith("https://")
    assert urls["Repository"].startswith("https://")
    assert urls["Issues"].startswith("https://")


def test_license_file_exists() -> None:
    license_text = Path("LICENSE").read_text()

    assert "MIT License" in license_text
    assert "Russ Davies" in license_text


def test_version_strategy_is_documented() -> None:
    release_text = Path("RELEASE.md").read_text()

    assert "## Versioning" in release_text
    assert "pyproject.toml" in release_text
    assert "__version__" in release_text
    assert "vMAJOR.MINOR.PATCH" in release_text
