from pathlib import Path


def test_release_workflow_is_manual_and_uses_trusted_publishing() -> None:
    text = Path(".github/workflows/release.yml").read_text()

    assert "workflow_dispatch:" in text
    assert "id-token: write" in text
    assert "pypa/gh-action-pypi-publish@release/v1" in text
    assert "environment: testpypi" in text
    assert "environment: pypi" in text
    assert "repository-url: https://test.pypi.org/legacy/" in text
    assert "python -m build" in text
    assert "python -m twine check dist/*" in text
    assert "python scripts/dogfood_external_project.py" in text


def test_release_workflow_checks_requested_version() -> None:
    text = Path(".github/workflows/release.yml").read_text()

    assert "Verify requested version matches package metadata" in text
    assert "pyproject.toml" in text
    assert "inputs.version" in text
    assert "Requested version" in text


def test_release_docs_reference_release_workflow_and_credentials() -> None:
    text = Path("RELEASE.md").read_text()

    for required in [
        ".github/workflows/release.yml",
        "trusted publishing",
        "workflow_dispatch",
        "testpypi",
        "pypi",
        "scoped API tokens",
        "__token__",
        "twine check dist/*",
    ]:
        assert required in text
