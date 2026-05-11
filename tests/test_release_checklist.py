from pathlib import Path


def test_release_checklist_exists_and_mentions_required_gates() -> None:
    text = Path("RELEASE.md").read_text()

    for required in [
        "ruff check .",
        "ruff format --check .",
        "mypy",
        "pytest",
        "python -m build",
        "TestPyPI",
        "PyPI",
    ]:
        assert required in text


def test_release_checklist_mentions_version_consistency() -> None:
    text = Path("RELEASE.md").read_text()

    assert "pyproject.toml" in text
    assert "__version__" in text
    assert "version consistency test" in text
