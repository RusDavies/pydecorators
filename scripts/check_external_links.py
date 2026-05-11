#!/usr/bin/env python3
"""Opt-in external HTTP(S) Markdown link checker for release maintenance."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "useful-decorators-link-checker/0.1"


def markdown_links(path: Path) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text())


def markdown_policy_files(root: Path) -> list[Path]:
    root_docs = sorted(root.glob("*.md"))
    docs_files = sorted((root / "docs").rglob("*.md"))
    return root_docs + docs_files


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


def external_http_links(root: Path) -> dict[Path, list[str]]:
    links_by_file: dict[Path, list[str]] = {}
    for docs_file in markdown_policy_files(root):
        links = [link for link in markdown_links(docs_file) if is_external_http_link(link)]
        if links:
            links_by_file[docs_file] = links
    return links_by_file


def check_url(url: str, timeout: float) -> tuple[bool, str]:
    request = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
    except HTTPError as error:
        if error.code in {405, 403}:
            get_request = Request(url, method="GET", headers={"User-Agent": USER_AGENT})
            try:
                with urlopen(get_request, timeout=timeout) as response:
                    status = response.status
            except (HTTPError, URLError, TimeoutError) as get_error:
                return False, str(get_error)
        else:
            return False, str(error)
    except (URLError, TimeoutError) as error:
        return False, str(error)

    if 200 <= status < 400:
        return True, str(status)
    return False, str(status)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--timeout", type=float, default=5.0, help="per-request timeout seconds")
    parser.add_argument(
        "--syntax-only",
        action="store_true",
        help="validate URL syntax without fetching the network",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    failures: list[str] = []
    checked = 0
    for docs_file, links in external_http_links(root).items():
        for link in links:
            checked += 1
            if not is_valid_external_http_link(link):
                failures.append(f"{docs_file}: invalid syntax: {link}")
                continue
            if args.syntax_only:
                continue
            ok, detail = check_url(link, args.timeout)
            if not ok:
                failures.append(f"{docs_file}: unreachable external link ({detail}): {link}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    mode = "syntax-checked" if args.syntax_only else "checked"
    print(f"{mode} {checked} external HTTP(S) link(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
