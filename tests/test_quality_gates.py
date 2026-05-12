from pathlib import Path


def test_pytest_enforces_coverage_floor_and_reports_xml() -> None:
    pyproject = Path("pyproject.toml").read_text()

    assert "--cov=useful_decorators" in pyproject
    assert "--cov-report=term-missing" in pyproject
    assert "--cov-report=xml" in pyproject
    assert "--cov-fail-under=90" in pyproject


def test_ci_runs_quality_gates_and_smoke_tests() -> None:
    ci = Path(".github/workflows/ci.yml").read_text()

    for required in [
        "ruff check .",
        "ruff format --check .",
        "mypy",
        "python scripts/smoke_imports.py",
        "python scripts/smoke_examples.py",
        "pytest",
        "python -m build",
    ]:
        assert required in ci


def test_smoke_scripts_exist() -> None:
    assert Path("scripts/smoke_imports.py").exists()
    assert Path("scripts/smoke_examples.py").exists()


def test_pre_commit_configuration_exists() -> None:
    config = Path(".pre-commit-config.yaml").read_text()

    assert "ruff-pre-commit" in config
    assert "ruff-format" in config
    assert "mirrors-mypy" in config
