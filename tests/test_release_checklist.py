from pathlib import Path

import pytest


def test_release_checklist_exists_and_mentions_required_gates() -> None:
    text = Path("RELEASE.md").read_text()

    for required in [
        "ruff check .",
        "ruff format --check .",
        "mypy",
        "pytest",
        "python -m build",
        "python scripts/smoke_wheel_install.py",
        "TestPyPI",
        "PyPI",
    ]:
        assert required in text


def test_release_checklist_mentions_version_consistency() -> None:
    text = Path("RELEASE.md").read_text()

    assert "pyproject.toml" in text
    assert "__version__" in text
    assert "version consistency test" in text


@pytest.mark.docs_policy
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


@pytest.mark.docs_policy
def test_docs_policy_script_exists_and_is_documented() -> None:
    release_text = Path("RELEASE.md").read_text()
    script = Path("scripts/docs-policy.sh")

    assert "./scripts/docs-policy.sh" in release_text
    assert script.exists()
    assert Path(".external-links-ignore").exists()
    script_text = script.read_text()
    assert "-m docs_policy" in script_text


@pytest.mark.docs_policy
def test_release_checklist_documents_optional_external_link_checker() -> None:
    release_text = Path("RELEASE.md").read_text()
    script = Path("scripts/check_external_links.py")

    assert "./scripts/check_external_links.py" in release_text
    assert "./scripts/check_external_links.py --syntax-only" in release_text
    assert "--syntax-only --verbose" in release_text
    assert ".external-links-ignore" in release_text
    assert "reason comment" in release_text
    assert "HTTP(S) URL pattern" in release_text
    assert "match at least one current external docs link" in release_text
    assert "--retries 4 --backoff 1.0" in release_text
    assert script.exists()
    assert Path(".external-links-ignore").exists()
    script_text = script.read_text()
    assert "urlopen" in script_text
    assert "--syntax-only" in script_text
    assert "--ignore-file" in script_text
    assert "--verbose" in script_text
    assert "--retries" in script_text
    assert "--backoff" in script_text


def test_release_checklist_documents_package_name_and_tagging() -> None:
    text = Path("RELEASE.md").read_text()

    assert "## Package name availability" in text
    assert "useful-decorators" in text
    assert "already occupied" in text
    assert "new distribution name" in text
    assert "## Tagging convention" in text
    assert "vMAJOR.MINOR.PATCH" in text
    assert "git tag -a v0.1.0" in text


def test_release_checklist_documents_persistent_cache_compatibility() -> None:
    text = Path("RELEASE.md").read_text()

    assert "## Persistent cache compatibility" in text
    for required in [
        "DiskCacheBackend",
        "cached value semantics",
        "payload shapes",
        "serializers",
        "trust boundaries",
        "bump the cache `namespace`",
        "cache_clear()",
        "backend `clear()`",
        "remove the SQLite cache file",
        "docs/disk_cache_backend.md",
    ]:
        assert required in text
