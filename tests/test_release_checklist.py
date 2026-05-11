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


def test_release_checklist_documents_docs_maintenance() -> None:
    text = Path("RELEASE.md").read_text()

    assert "## Documentation maintenance" in text
    for required in [
        "docs/index.md",
        "docs/examples/",
        "tests/test_docs_examples.py",
        "Local Markdown links",
        "GOAL.md",
        "PLAN.md",
        "TODO.md",
    ]:
        assert required in text


def test_docs_policy_script_exists_and_is_documented() -> None:
    release_text = Path("RELEASE.md").read_text()
    script = Path("scripts/docs-policy.sh")

    assert "./scripts/docs-policy.sh" in release_text
    assert script.exists()
    script_text = script.read_text()
    for required in [
        "tests/test_public_api_policy.py",
        "tests/test_docs_examples.py",
        "tests/test_release_checklist.py",
    ]:
        assert required in script_text
