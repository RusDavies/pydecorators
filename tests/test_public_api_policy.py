import ast
import inspect
import re
from pathlib import Path

import useful_decorators


def documented_public_api_names() -> set[str]:
    text = Path("docs/PUBLIC_API.md").read_text()
    section = text.split("## Internal API", maxsplit=1)[0]
    return set(re.findall(r"^- `([^`]+)`", section, flags=re.MULTILINE))


def public_api_note_for(name: str) -> str:
    public_api = Path("docs/PUBLIC_API.md").read_text()
    match = re.search(
        rf"^### `{re.escape(name)}`\n(?P<body>.*?)(?=^### `|\Z)",
        public_api,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def public_example_functions(example_path: Path) -> set[str]:
    tree = ast.parse(example_path.read_text())
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    }


def test_documented_public_api_matches_all_exports() -> None:
    assert documented_public_api_names() == set(useful_decorators.__all__)


def test_ci_matrix_includes_minimum_supported_python_version() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text()
    pyproject = Path("pyproject.toml").read_text()

    assert 'requires-python = ">=3.11"' in pyproject
    assert '"3.11"' in workflow


def test_public_exceptions_are_documented_in_public_api_notes() -> None:
    public_api = Path("docs/PUBLIC_API.md").read_text()
    public_exception_names = {
        name
        for name in useful_decorators.__all__
        if inspect.isclass(getattr(useful_decorators, name))
        and issubclass(getattr(useful_decorators, name), BaseException)
    }

    assert public_exception_names
    for name in public_exception_names:
        assert f"### `{name}`" in public_api


def test_public_exception_inheritance_matches_documentation() -> None:
    inheritance_phrases: dict[type[BaseException], str] = {
        useful_decorators.UsefulDecoratorsError: "base class for package-specific exceptions",
        useful_decorators.ConfigurationError: "ValueError",
        useful_decorators.RateLimitExceeded: "UsefulDecoratorsError",
        useful_decorators.FunctionTimedOut: "TimeoutError",
        useful_decorators.CacheKeyError: "TypeError",
        useful_decorators.CacheSerializationError: "UsefulDecoratorsError",
        useful_decorators.CacheBackendClosedError: "UsefulDecoratorsError",
    }

    for exception_type, expected_phrase in inheritance_phrases.items():
        note = public_api_note_for(exception_type.__name__)
        assert expected_phrase in note


def test_public_exceptions_reference_covers_public_exceptions() -> None:
    exceptions_reference = Path("docs/exceptions.md").read_text()
    public_exception_names = {
        name
        for name in useful_decorators.__all__
        if inspect.isclass(getattr(useful_decorators, name))
        and issubclass(getattr(useful_decorators, name), BaseException)
    }

    assert "docs/examples/public_exception_examples.py" in exceptions_reference
    for name in public_exception_names:
        assert f"`{name}`" in exceptions_reference


def docs_index_local_links() -> set[Path]:
    docs_index = Path("docs/index.md")
    text = docs_index.read_text()
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)

    assert links
    return {
        docs_index.parent / link.split("#", maxsplit=1)[0]
        for link in links
        if "://" not in link and not link.startswith("#")
    }


def test_docs_index_links_resolve_to_existing_files() -> None:
    for target in docs_index_local_links():
        assert target.exists(), f"missing docs index target: {target}"


def test_top_level_docs_markdown_files_are_linked_from_docs_index() -> None:
    explicitly_exempt = {Path("docs/index.md")}
    top_level_docs = {path for path in Path("docs").glob("*.md")}
    linked_docs = {path for path in docs_index_local_links() if path.suffix == ".md"}

    assert top_level_docs - explicitly_exempt <= linked_docs


def test_docs_examples_are_listed_from_docs_index() -> None:
    explicitly_exempt = {Path("docs/examples/__init__.py")}
    example_files = {path for path in Path("docs/examples").glob("*.py")}
    linked_examples = {
        path for path in docs_index_local_links() if path.parent == Path("docs/examples")
    }

    assert example_files - explicitly_exempt == linked_examples


def test_docs_examples_are_exercised_by_docs_example_tests() -> None:
    explicitly_exempt = {Path("docs/examples/__init__.py")}
    example_files = {path for path in Path("docs/examples").glob("*.py")}
    docs_example_tests = Path("tests/test_docs_examples.py").read_text()
    exercised_examples = {
        Path("docs/examples") / f"{module_name}.py"
        for module_name in re.findall(r"load_docs_example\(\"([^\"]+)\"\)", docs_example_tests)
    }

    assert example_files - explicitly_exempt == exercised_examples


def test_public_docs_example_functions_have_assertions() -> None:
    explicitly_exempt = {Path("docs/examples/__init__.py")}
    example_files = sorted(set(Path("docs/examples").glob("*.py")) - explicitly_exempt)
    docs_example_tests = Path("tests/test_docs_examples.py").read_text()

    for example_path in example_files:
        module_name = example_path.stem
        for function_name in public_example_functions(example_path):
            expected_call = f"examples.{function_name}("
            assert expected_call in docs_example_tests, (
                f"missing assertion call for {module_name}.{function_name}"
            )


def test_docs_example_filenames_follow_convention() -> None:
    explicitly_exempt = {Path("docs/examples/__init__.py")}
    example_files = set(Path("docs/examples").glob("*.py")) - explicitly_exempt

    assert example_files
    for example_path in example_files:
        assert example_path.name.endswith("_examples.py")


def test_docs_index_links_to_executable_example_conventions() -> None:
    docs_index = Path("docs/index.md").read_text()
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "../CONTRIBUTING.md#executable-documentation-examples" in docs_index
    assert "## Executable documentation examples" in contributing
