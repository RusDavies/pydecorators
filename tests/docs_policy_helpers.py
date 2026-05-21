import re
from pathlib import Path
from urllib.parse import urlparse

REPO_BLOB_BASE = "https://github.com/RusDavies/pydecorators/blob/master/"
REPO_TREE_BASE = "https://github.com/RusDavies/pydecorators/tree/master/"

DOCS_INDEX_EXEMPTIONS = {
    Path("docs/index.md"),
}


def markdown_links(path: Path) -> list[str]:
    text = path.read_text()
    inline_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    reference_links = re.findall(
        r"^\s*\[[^\]]+\]:\s+(\S+)",
        text,
        flags=re.MULTILINE,
    )
    return inline_links + reference_links


def markdown_policy_files() -> list[Path]:
    root_docs = sorted(Path(".").glob("*.md"))
    docs_files = sorted(Path("docs").rglob("*.md"))
    return root_docs + docs_files


def docs_index_markdown_links() -> list[str]:
    links = markdown_links(Path("docs/index.md"))

    assert links
    return links


def is_external_or_page_anchor(link: str) -> bool:
    return link.startswith("#") or ("://" in link and github_repo_link_path(link) is None)


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
    github_path = github_repo_link_path(link)
    if github_path is not None:
        return github_path
    path_part = link.split("#", maxsplit=1)[0]
    return source.parent / path_part


def github_repo_link_path(link: str) -> Path | None:
    link_without_fragment = link.split("#", maxsplit=1)[0]
    for base in (REPO_BLOB_BASE, REPO_TREE_BASE):
        if link_without_fragment.startswith(base):
            return Path(link_without_fragment.removeprefix(base))
    return None


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
