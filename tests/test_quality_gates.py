from pathlib import Path


def test_pytest_enforces_coverage_floor_and_reports_xml() -> None:
    pyproject = Path("pyproject.toml").read_text()

    assert "--cov=pydecorators" in pyproject
    assert "--cov-report=term-missing" in pyproject
    assert "--cov-report=xml" in pyproject
    assert "--cov-fail-under=90" in pyproject


def test_ci_runs_quality_gates_and_smoke_tests() -> None:
    ci = Path(".github/workflows/ci.yml").read_text()

    for required in [
        "pytest -m docs_policy",
        "ruff check .",
        "ruff format --check .",
        "mypy",
        "python scripts/smoke_imports.py",
        "python scripts/smoke_examples.py",
        "pytest",
        "actions/upload-artifact@v4",
        "coverage.xml",
        "python -m build",
        "python scripts/smoke_wheel_install.py",
        "python scripts/dogfood_local_wheel.py",
        "python scripts/dogfood_external_project.py",
    ]:
        assert required in ci


def test_smoke_scripts_exist() -> None:
    assert Path("scripts/smoke_imports.py").exists()
    assert Path("scripts/smoke_examples.py").exists()
    assert Path("scripts/smoke_wheel_install.py").exists()
    assert Path("scripts/dogfood_local_wheel.py").exists()
    assert Path("scripts/dogfood_external_project.py").exists()


def test_pre_commit_configuration_exists() -> None:
    config = Path(".pre-commit-config.yaml").read_text()

    assert "ruff-pre-commit" in config
    assert "ruff-format" in config
    assert "mirrors-mypy" in config


def test_pull_request_template_includes_docs_policy_checkboxes() -> None:
    text = Path(".github/pull_request_template.md").read_text()

    for required in [
        "docs/index.md",
        "tests/test_docs_examples.py",
        "docs_policy",
        "./scripts/docs-policy.sh",
        "RELEASE.md",
        "TODO.md",
    ]:
        assert required in text


def test_pyproject_exposes_docs_policy_hatch_alias() -> None:
    pyproject = Path("pyproject.toml").read_text()
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "[tool.hatch.envs.default.scripts]" in pyproject
    assert 'docs-policy = "./scripts/docs-policy.sh"' in pyproject
    assert "hatch run docs-policy" in contributing


def test_hatch_full_gate_alias_matches_release_prep_commands() -> None:
    pyproject = Path("pyproject.toml").read_text()

    for command in [
        "./scripts/docs-policy.sh",
        "ruff check .",
        "ruff format --check .",
        "mypy",
        "python scripts/smoke_imports.py",
        "python scripts/smoke_examples.py",
        "pytest",
        "python -m build",
        "python scripts/smoke_wheel_install.py",
        "python scripts/dogfood_local_wheel.py",
        "python scripts/dogfood_external_project.py",
    ]:
        assert command in pyproject


def test_quality_gates_documents_external_link_ignore_wildcards() -> None:
    text = Path("docs/quality_gates.md").read_text()

    for required in [
        "External link ignore wildcards",
        ".external-links-ignore",
        "fnmatch",
        "https://vendor.example.com/docs/*",
        "case-sensitive",
        "reason comment",
    ]:
        assert required in text


def test_coverage_summary_script_reports_line_coverage(tmp_path: Path) -> None:
    import subprocess
    import sys

    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        "<?xml version='1.0' ?>\n"
        "<coverage line-rate='0.9721' branch-rate='0' version='7'></coverage>\n"
    )

    result = subprocess.run(
        [sys.executable, "scripts/coverage_summary.py", str(coverage_xml)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "## Coverage" in result.stdout
    assert "Line coverage: 97.21%" in result.stdout
