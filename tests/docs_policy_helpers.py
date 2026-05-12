import ast
import re
from pathlib import Path
from urllib.parse import urlparse


def asserted_example_function_calls(test_path: Path) -> set[str]:
    tree = ast.parse(test_path.read_text())
    calls: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id == "examples":
            calls.add(node.func.attr)

    return calls


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


def is_external_http_link(link: str) -> bool:
    parsed = urlparse(link)
    return parsed.scheme in {"http", "https"}


def is_valid_external_http_link(link: str) -> bool:
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    return not any(character.isspace() for character in link)


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
    return anchor.strip("-")


def markdown_heading_anchors(path: Path) -> set[str]:
    headings = re.findall(r"^#{1,6}\s+(.+)$", path.read_text(), flags=re.MULTILINE)
    anchors: set[str] = set()
    seen_counts: dict[str, int] = {}

    for heading in headings:
        base_anchor = markdown_heading_anchor(heading)
        count = seen_counts.get(base_anchor, 0)
        seen_counts[base_anchor] = count + 1
        anchor = base_anchor if count == 0 else f"{base_anchor}-{count}"
        anchors.add(anchor)

    return anchors
