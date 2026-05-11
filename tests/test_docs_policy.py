import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_policy


def public_example_functions(example_path: Path) -> set[str]:
    tree = ast.parse(example_path.read_text())
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    }


def markdown_links(path: Path) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text())


def markdown_policy_files() -> list[Path]:
    root_docs = sorted(Path(".").glob("*.md"))
    docs_files = sorted(Path("docs").rglob("*.md"))
    return root_docs + docs_files


def docs_index_markdown_links() -> list[str]:
    links = markdown_links(Path("docs/index.md"))

    assert links
    return links


def is_external_or_page_anchor(link: str) -> bool:
    return "://" in link or link.startswith("#")


def local_link_path(source: Path, link: str) -> Path:
    path_part = link.split("#", maxsplit=1)[0]
    return source.parent / path_part


def docs_index_local_links() -> set[Path]:
    docs_index = Path("docs/index.md")
    return {
        local_link_path(docs_index, link)
        for link in docs_index_markdown_links()
        if not is_external_or_page_anchor(link)
    }


def markdown_heading_anchor(heading: str) -> str:
    anchor = heading.strip().lower()
    anchor = re.sub(r"[^a-z0-9 _-]", "", anchor)
    anchor = anchor.replace(" ", "-")
    anchor = re.sub(r"-+", "-", anchor)
    return anchor


def markdown_heading_anchors(path: Path) -> set[str]:
    headings = re.findall(r"^#{1,6}\s+(.+)$", path.read_text(), flags=re.MULTILINE)
    return {markdown_heading_anchor(heading) for heading in headings}


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


def test_docs_index_local_markdown_fragment_links_resolve() -> None:
    docs_index = Path("docs/index.md")
    fragment_links = [
        link
        for link in docs_index_markdown_links()
        if "://" not in link and "#" in link and not link.startswith("#")
    ]

    assert fragment_links
    for link in fragment_links:
        path_part, fragment = link.split("#", maxsplit=1)
        target = docs_index.parent / path_part
        assert target.suffix == ".md"
        assert fragment in markdown_heading_anchors(target), (
            f"missing Markdown anchor target: {link}"
        )


def test_all_docs_local_markdown_links_resolve() -> None:
    docs_files = markdown_policy_files()

    assert docs_files
    for docs_file in docs_files:
        for link in markdown_links(docs_file):
            if is_external_or_page_anchor(link):
                continue
            target = local_link_path(docs_file, link)
            assert target.exists(), f"missing local docs link target: {docs_file}: {link}"


def test_all_docs_local_markdown_fragment_links_resolve() -> None:
    docs_files = markdown_policy_files()

    assert docs_files
    for docs_file in docs_files:
        for link in markdown_links(docs_file):
            if is_external_or_page_anchor(link) or "#" not in link:
                continue
            target = local_link_path(docs_file, link)
            if target.suffix != ".md":
                continue
            _, fragment = link.split("#", maxsplit=1)
            assert fragment in markdown_heading_anchors(target), (
                f"missing Markdown anchor target: {docs_file}: {link}"
            )


def test_root_docs_link_to_docs_index_where_appropriate() -> None:
    root_docs_that_should_link_index = {
        Path("README.md"),
        Path("CONTRIBUTING.md"),
        Path("RELEASE.md"),
    }

    for root_doc in root_docs_that_should_link_index:
        assert "docs/index.md" in root_doc.read_text()


def test_contributing_documents_root_docs_index_link_policy() -> None:
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "## Root documentation links" in contributing
    assert (
        "Root docs that help users or contributors navigate the project should link "
        "to `docs/index.md`." in contributing
    )
    for required_root_doc in ("README.md", "CONTRIBUTING.md", "RELEASE.md"):
        assert f"- `{required_root_doc}`" in contributing


def test_contributing_documents_docs_policy_marker_guidance() -> None:
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "## Documentation policy tests" in contributing
    assert "`docs_policy` pytest marker" in contributing
    for required in [
        "docs/index.md",
        "executable documentation example",
        "Markdown local-link",
        "root documentation link policy",
        "release-checklist documentation maintenance",
        "./scripts/docs-policy.sh",
    ]:
        assert required in contributing


def test_contributing_documents_docs_file_update_checklist() -> None:
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "## Adding or changing documentation files" in contributing
    for required in [
        "new top-level `docs/*.md` pages",
        "docs/index.md",
        "docs/examples/",
        "tests/test_docs_examples.py",
        "pytest.mark.docs_policy",
        "./scripts/docs-policy.sh",
        "GOAL.md",
        "PLAN.md",
        "TODO.md",
    ]:
        assert required in contributing
