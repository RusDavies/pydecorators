import tomllib
from pathlib import Path

import useful_decorators


def test_package_version_matches_project_metadata() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert useful_decorators.__version__ == pyproject["project"]["version"]
