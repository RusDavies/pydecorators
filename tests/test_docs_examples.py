import importlib.util
import warnings
from pathlib import Path
from types import ModuleType


def load_deprecated_examples() -> ModuleType:
    example_path = Path("docs/examples/deprecated_examples.py")
    spec = importlib.util.spec_from_file_location("deprecated_examples", example_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deprecated_documentation_examples_execute() -> None:
    examples = load_deprecated_examples()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert examples.old_bare_function(1, 2) == 3
        assert examples.old_configured_function(1, 2) == 3
        assert examples.Client().fetch_old() == "old"
