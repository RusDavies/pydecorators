#!/usr/bin/env python3
"""Opt-in external HTTP(S) Markdown link checker for release maintenance."""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "useful-decorators-link-checker/0.1"
DEFAULT_IGNORE_FILE = ".external-links-ignore"


def is_valid_external_http_pattern(pattern: str) -> bool:
    parsed = urlparse(pattern)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    return not any(character.isspace() for character in pattern)


def ignore_file_errors(path: Path) -> list[str]:
    if not path.exists():
        return []

    errors: list[str] = []
    previous_meaningful_line_was_comment = False
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            previous_meaningful_line_was_comment = False
            continue
        if line.startswith("#"):
            previous_meaningful_line_was_comment = True
            continue
        if not previous_meaningful_line_was_comment:
            errors.append(
                f"{path}:{line_number}: ignore pattern must be preceded by a reason comment"
            )
        if not is_valid_external_http_pattern(line):
            errors.append(f"{path}:{line_number}: ignore pattern must be an HTTP(S) URL pattern")
        previous_meaningful_line_was_comment = False

    return errors


def ignore_file_reason_errors(path: Path) -> list[str]:
    return [
        error
        for error in ignore_file_errors(path)
        if "must be preceded by a reason comment" in error
    ]


def load_ignore_patterns(path: Path) -> list[str]:
    if not path.exists():
        return []
    patterns: list[str] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def ignored_link_pattern(link: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if fnmatch.fnmatchcase(link, pattern):
            return pattern
    return None


def is_ignored_link(link: str, patterns: list[str]) -> bool:
    return ignored_link_pattern(link, patterns) is not None


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


def is_retryable_status(status: int) -> bool:
    return status in {408, 429} or 500 <= status < 600


def check_url_once(url: str, timeout: float) -> tuple[bool, str, bool]:
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
            except HTTPError as get_error:
                return False, str(get_error), is_retryable_status(get_error.code)
            except (URLError, TimeoutError) as get_error:
                return False, str(get_error), True
        else:
            return False, str(error), is_retryable_status(error.code)
    except (URLError, TimeoutError) as error:
        return False, str(error), True

    if 200 <= status < 400:
        return True, str(status), False
    return False, str(status), is_retryable_status(status)


def check_url(
    url: str,
    timeout: float,
    retries: int,
    backoff: float,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[bool, str]:
    attempts = max(1, retries + 1)
    last_detail = "not checked"

    for attempt in range(attempts):
        ok, detail, retryable = check_url_once(url, timeout)
        if ok:
            return True, detail
        last_detail = detail
        if not retryable or attempt == attempts - 1:
            break
        sleep(backoff * (2**attempt))

    return False, f"{last_detail} after {attempt + 1} attempt(s)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--timeout", type=float, default=5.0, help="per-request timeout seconds")
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="retry attempts for transient failures before reporting a link as unreachable",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=0.5,
        help="initial retry backoff seconds; doubles after each transient failure",
    )
    parser.add_argument(
        "--syntax-only",
        action="store_true",
        help="validate URL syntax without fetching the network",
    )
    parser.add_argument(
        "--ignore-file",
        type=Path,
        default=Path(DEFAULT_IGNORE_FILE),
        help=(
            "file of external link ignore patterns, one fnmatch-style pattern per line; "
            "defaults to .external-links-ignore"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print checked and ignored external links during manual release checks",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    ignore_file = args.ignore_file
    if not ignore_file.is_absolute():
        ignore_file = root / ignore_file
    ignore_errors = ignore_file_errors(ignore_file)
    if ignore_errors:
        for error in ignore_errors:
            print(error, file=sys.stderr)
        return 1

    ignore_patterns = load_ignore_patterns(ignore_file)
    failures: list[str] = []
    checked = 0
    ignored = 0
    ignored_links: list[str] = []
    for docs_file, links in external_http_links(root).items():
        for link in links:
            ignore_pattern = ignored_link_pattern(link, ignore_patterns)
            if ignore_pattern is not None:
                ignored += 1
                ignored_links.append(f"ignored {docs_file}: {link} (matched {ignore_pattern})")
                continue
            checked += 1
            if args.verbose:
                print(f"checking {docs_file}: {link}")
            if not is_valid_external_http_link(link):
                failures.append(f"{docs_file}: invalid syntax: {link}")
                continue
            if args.syntax_only:
                continue
            ok, detail = check_url(link, args.timeout, args.retries, args.backoff)
            if not ok:
                failures.append(f"{docs_file}: unreachable external link ({detail}): {link}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    if args.verbose:
        for ignored_link in ignored_links:
            print(ignored_link)

    mode = "syntax-checked" if args.syntax_only else "checked"
    ignored_message = f"; ignored {ignored}" if ignored else ""
    print(f"{mode} {checked} external HTTP(S) link(s){ignored_message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
