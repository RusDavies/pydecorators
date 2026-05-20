import tomllib
from pathlib import Path

import pydecorators


def test_package_version_matches_project_metadata() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert pydecorators.__version__ == pyproject["project"]["version"]
