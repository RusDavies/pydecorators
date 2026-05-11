import importlib.util
import warnings
from pathlib import Path
from types import ModuleType


def load_docs_example(module_name: str) -> ModuleType:
    example_path = Path("docs/examples") / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, example_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deprecated_documentation_examples_execute() -> None:
    examples = load_docs_example("deprecated_examples")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert examples.old_bare_function(1, 2) == 3
        assert examples.old_configured_function(1, 2) == 3
        assert examples.Client().fetch_old() == "old"


def test_disk_cache_backend_documentation_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    first, second, calls = examples.disk_cache_example(tmp_path / "cache.sqlite3")

    assert first == "User user-123"
    assert second == "User user-123"
    assert calls == 1


def test_disk_cache_backend_context_manager_documentation_example_executes(
    tmp_path: Path,
) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    value, hits = examples.scoped_disk_cache_example(tmp_path / "scoped-cache.sqlite3")

    assert value == "cached"
    assert hits == 1


def test_cache_backend_closed_error_documentation_example_executes(tmp_path: Path) -> None:
    examples = load_docs_example("disk_cache_backend_examples")

    assert examples.closed_backend_error_example(tmp_path / "closed-cache.sqlite3") == "closed"


def test_public_exception_documentation_examples_execute() -> None:
    examples = load_docs_example("public_exception_examples")

    assert examples.configuration_error_example() == "invalid configuration"
    assert examples.cache_key_error_example() == "unhashable key"
    assert examples.cache_serialization_error_example() == "serialization failed"
