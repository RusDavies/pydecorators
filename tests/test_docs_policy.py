import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

from tests.docs_policy_helpers import (
    DOCS_INDEX_EXEMPTIONS,
    asserted_example_function_calls,
    docs_index_local_links,
    docs_index_markdown_links,
    is_external_http_link,
    is_external_or_page_anchor,
    is_valid_external_http_link,
    local_link_path,
    markdown_heading_anchor,
    markdown_heading_anchors,
    markdown_links,
    markdown_policy_files,
    public_example_functions,
)

pytestmark = pytest.mark.docs_policy


def readme_python_code_blocks() -> list[str]:
    return re.findall(
        r"```python\n(.*?)\n```",
        Path("README.md").read_text(),
        flags=re.DOTALL,
    )


def docs_index_section_links(section_name: str) -> list[str]:
    docs_index = Path("docs/index.md").read_text()
    match = re.search(
        rf"^## {re.escape(section_name)}\n(?P<body>.*?)(?=^## |\Z)",
        docs_index,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing docs index section: {section_name}"
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", match.group("body"))


def load_external_link_checker_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_external_links", "scripts/check_external_links.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_docs_index_sections_follow_expected_classification() -> None:
    expected_sections = [
        "Core project docs",
        "Decorator docs",
        "Cache backend docs",
        "Executable examples",
    ]
    docs_index = Path("docs/index.md").read_text()
    actual_sections = re.findall(r"^## (.+)$", docs_index, flags=re.MULTILINE)

    assert actual_sections == expected_sections

    assert "cache_result.md" not in docs_index_section_links("Core project docs")
    assert "disk_cache_backend.md" in docs_index_section_links("Cache backend docs")
    for link in docs_index_section_links("Decorator docs"):
        assert link.endswith(".md")
        assert link not in {"PUBLIC_API.md", "API_REFERENCE.md", "API_DESIGN.md"}
    for link in docs_index_section_links("Executable examples"):
        if link.startswith("examples/") and link != "examples/":
            assert link.endswith("_examples.py")


def test_docs_index_links_resolve_to_existing_files() -> None:
    for target in docs_index_local_links():
        assert target.exists(), f"missing docs index target: {target}"


def test_top_level_docs_markdown_files_are_linked_from_docs_index() -> None:
    top_level_docs = {path for path in Path("docs").glob("*.md")}
    linked_docs = {path for path in docs_index_local_links() if path.suffix == ".md"}

    assert top_level_docs - DOCS_INDEX_EXEMPTIONS <= linked_docs


def test_docs_index_exemptions_are_intentional_docs_files() -> None:
    assert {Path("docs/index.md")} == DOCS_INDEX_EXEMPTIONS
    for exempt_path in DOCS_INDEX_EXEMPTIONS:
        assert exempt_path.exists()
        assert exempt_path.suffix == ".md"


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
    exercised_module_names = set(
        re.findall(r"load_docs_example\(\"([^\"]+)\"\)", docs_example_tests)
    ) | set(re.findall(r'\("([^\"]+_examples)"', docs_example_tests))
    exercised_examples = {
        Path("docs/examples") / f"{module_name}.py" for module_name in exercised_module_names
    }

    assert example_files - explicitly_exempt == exercised_examples


def test_public_docs_example_functions_have_assertions() -> None:
    explicitly_exempt = {Path("docs/examples/__init__.py")}
    example_files = sorted(set(Path("docs/examples").glob("*.py")) - explicitly_exempt)
    asserted_calls = asserted_example_function_calls(Path("tests/test_docs_examples.py"))

    for example_path in example_files:
        module_name = example_path.stem
        for function_name in public_example_functions(example_path):
            assert function_name in asserted_calls, (
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


def test_external_http_markdown_links_are_syntax_checked_without_fetching() -> None:
    docs_files = markdown_policy_files()

    assert docs_files
    for docs_file in docs_files:
        for link in markdown_links(docs_file):
            if is_external_http_link(link):
                assert is_valid_external_http_link(link), (
                    f"invalid external HTTP(S) link syntax: {docs_file}: {link}"
                )


def test_external_http_link_helper_rejects_invalid_urls() -> None:
    assert is_valid_external_http_link("https://example.com/docs")
    assert is_valid_external_http_link("http://example.com/path?query=value#anchor")
    assert not is_valid_external_http_link("https:///missing-host")
    assert not is_valid_external_http_link("https://example.com/bad path")
    assert not is_valid_external_http_link("ftp://example.com/file")


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


def test_readme_python_code_blocks_parse() -> None:
    import ast

    code_blocks = readme_python_code_blocks()

    assert len(code_blocks) == 12
    for code_block in code_blocks:
        ast.parse(code_block)


def test_readme_python_code_blocks_stay_synced_with_documented_examples() -> None:
    code_blocks = readme_python_code_blocks()
    joined_blocks = "\n\n".join(code_blocks)

    for required in [
        "from useful_decorators import deprecated",
        "@deprecated(",
        "from useful_decorators import retry",
        "@retry(attempts=3, delay=0.25, backoff=2, exceptions=ConnectionError)",
        "from useful_decorators import rate_limit",
        "@rate_limit(calls=10, period=60, key=lambda user_id: user_id)",
        "from useful_decorators import timeout",
        "@timeout(seconds=2)",
        "from useful_decorators import log_calls",
        '@log_calls(include_args=True, redact_args={"password"})',
        "from useful_decorators import TimingInfo, measure_time",
        "@measure_time(callback=timings.append)",
        "from useful_decorators import validate_types",
        "@validate_types(validate_return=True)",
        "from useful_decorators import require_env",
        '@require_env("API_TOKEN")',
        "from useful_decorators import CircuitBreakerOpen, circuit_breaker",
        "@circuit_breaker(failure_threshold=2, reset_timeout=10)",
        "from useful_decorators import cache_result",
        "@cache_result(maxsize=128)",
        "from useful_decorators import DiskCacheBackend, cache_result",
        "DiskCacheBackend(",
        '@cache_result(backend=backend, namespace="users")',
        "finally:",
        "backend.close()",
    ]:
        assert required in joined_blocks


def test_readme_disk_cache_code_block_matches_lifecycle_guidance() -> None:
    disk_cache_block = next(
        block for block in readme_python_code_blocks() if "DiskCacheBackend" in block
    )

    assert "backend = DiskCacheBackend" in disk_cache_block
    assert 'namespace="users"' in disk_cache_block
    assert "try:" in disk_cache_block
    assert "finally:" in disk_cache_block
    assert disk_cache_block.index("try:") < disk_cache_block.index("finally:")
    assert disk_cache_block.index("finally:") < disk_cache_block.index("backend.close()")


README_CORE_DOC_LINKS = [
    "docs/index.md",
    "docs/PUBLIC_API.md",
    "docs/API_DESIGN.md",
    "docs/exceptions.md",
    "docs/deprecated.md",
    "docs/cache_result.md",
    "docs/disk_cache_backend.md",
]


def test_readme_links_to_core_docs_pages() -> None:
    readme = Path("README.md").read_text()

    assert "## Documentation" in readme
    for required_link in README_CORE_DOC_LINKS:
        assert required_link in readme


def test_contributing_documents_readme_core_doc_links() -> None:
    contributing = Path("CONTRIBUTING.md").read_text()

    for required_link in README_CORE_DOC_LINKS:
        assert required_link in contributing


def test_contributing_documents_docs_index_inclusion_rule() -> None:
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "## Documentation index inclusion rule" in contributing
    for required in [
        "intended to help users or contributors",
        "public API",
        "per-decorator behavior docs",
        "cache backend",
        "executable documentation examples",
        "release, contribution, or documentation-maintenance guidance",
        "GOAL.md",
        "PLAN.md",
        "TODO.md",
        "intentionally not indexed",
        "docs_policy",
    ]:
        assert required in contributing


def test_markdown_links_include_reference_style_links(tmp_path: Path) -> None:
    markdown_file = tmp_path / "reference-links.md"
    markdown_file.write_text(
        "See [inline](docs/index.md) and [reference][docs-index].\n\n"
        "[docs-index]: docs/index.md#core-project-docs\n"
    )

    assert markdown_links(markdown_file) == [
        "docs/index.md",
        "docs/index.md#core-project-docs",
    ]


def test_markdown_heading_anchor_helper_matches_expected_slug_shape() -> None:
    assert markdown_heading_anchor("Cache Backend: WAL & Busy Timeout!") == (
        "cache-backend-wal-busy-timeout"
    )


def test_markdown_heading_anchor_helper_handles_non_ascii_headings() -> None:
    assert markdown_heading_anchor("Café naïve façade — 版本") == "caf-nave-faade"


def test_markdown_heading_anchors_include_duplicate_heading_suffixes(tmp_path: Path) -> None:
    markdown_file = tmp_path / "duplicate-headings.md"
    markdown_file.write_text("# Examples\n## Details\n## Examples\n### Examples\n## Details\n")

    assert markdown_heading_anchors(markdown_file) == {
        "examples",
        "details",
        "examples-1",
        "examples-2",
        "details-1",
    }


def test_external_link_checker_rejects_unapproved_non_http_schemes(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[email](mailto:security@example.com)\n")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "unsupported external link scheme 'mailto'" in result.stderr


def test_external_link_checker_allows_intentional_non_http_schemes(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[email](mailto:security@example.com)\n")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
            "--allow-scheme",
            "mailto",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "syntax-checked 0 external HTTP(S) link(s)" in result.stdout


def test_external_link_checker_syntax_only_mode_passes_without_network() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/check_external_links.py", "--syntax-only"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "syntax-checked" in result.stdout


def test_external_link_checker_retries_transient_failures_with_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = load_external_link_checker_module()
    attempts = 0
    sleeps: list[float] = []

    def fake_check_url_once(url: str, timeout: float) -> tuple[bool, str, bool]:
        nonlocal attempts
        attempts += 1
        assert url == "https://example.com"
        assert timeout == 3.0
        if attempts < 3:
            return False, "temporary outage", True
        return True, "200", False

    monkeypatch.setattr(checker, "check_url_once", fake_check_url_once)

    ok, detail = checker.check_url(
        "https://example.com",
        timeout=3.0,
        retries=3,
        backoff=0.25,
        sleep=sleeps.append,
    )

    assert ok
    assert detail == "200"
    assert attempts == 3
    assert sleeps == [0.25, 0.5]


def test_external_link_checker_does_not_retry_non_retryable_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = load_external_link_checker_module()
    attempts = 0
    sleeps: list[float] = []

    def fake_check_url_once(url: str, timeout: float) -> tuple[bool, str, bool]:
        nonlocal attempts
        attempts += 1
        return False, "HTTP Error 404: Not Found", False

    monkeypatch.setattr(checker, "check_url_once", fake_check_url_once)

    ok, detail = checker.check_url(
        "https://example.com/missing",
        timeout=3.0,
        retries=3,
        backoff=0.25,
        sleep=sleeps.append,
    )

    assert not ok
    assert detail == "HTTP Error 404: Not Found after 1 attempt(s)"
    assert attempts == 1
    assert sleeps == []


def test_external_link_checker_caps_retry_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = load_external_link_checker_module()
    attempts = 0
    sleeps: list[float] = []

    def fake_check_url_once(url: str, timeout: float) -> tuple[bool, str, bool]:
        nonlocal attempts
        attempts += 1
        if attempts < 4:
            return False, "temporary outage", True
        return True, "200", False

    monkeypatch.setattr(checker, "check_url_once", fake_check_url_once)

    ok, detail = checker.check_url(
        "https://example.com",
        timeout=3.0,
        retries=3,
        backoff=0.5,
        max_backoff=0.75,
        sleep=sleeps.append,
    )

    assert ok
    assert detail == "200"
    assert sleeps == [0.5, 0.75, 0.75]


def test_external_link_checker_reports_verbose_attempt_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = load_external_link_checker_module()
    attempts = 0
    sleeps: list[float] = []
    reports: list[str] = []

    def fake_check_url_once(url: str, timeout: float) -> tuple[bool, str, bool]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return False, "HTTP Error 503: Service Unavailable", True
        return True, "200", False

    monkeypatch.setattr(checker, "check_url_once", fake_check_url_once)

    ok, detail = checker.check_url(
        "https://example.com",
        timeout=3.0,
        retries=1,
        backoff=0.25,
        sleep=sleeps.append,
        report_attempt=reports.append,
    )

    assert ok
    assert detail == "200"
    assert sleeps == [0.25]
    assert reports == [
        "attempt 1/2: failed retryable: HTTP Error 503: Service Unavailable",
        "attempt 2/2: ok: 200",
    ]


def test_external_link_checker_loads_ignore_patterns(tmp_path: Path) -> None:
    checker = load_external_link_checker_module()
    ignore_file = tmp_path / "external-links.ignore"
    ignore_file.write_text(
        "# comment\n\nhttps://unstable.example.com/*\nhttps://example.com/exact\n"
    )

    assert checker.load_ignore_patterns(ignore_file) == [
        "https://unstable.example.com/*",
        "https://example.com/exact",
    ]
    assert checker.load_ignore_patterns(tmp_path / "missing.ignore") == []


def test_external_link_checker_matches_ignore_patterns() -> None:
    checker = load_external_link_checker_module()
    patterns = ["https://unstable.example.com/*", "https://example.com/exact"]

    assert checker.ignored_link_pattern("https://unstable.example.com/docs", patterns) == (
        "https://unstable.example.com/*"
    )
    assert checker.ignored_link_pattern("https://example.com/exact", patterns) == (
        "https://example.com/exact"
    )
    assert checker.ignored_link_pattern("https://example.com/other", patterns) is None
    assert checker.is_ignored_link("https://unstable.example.com/docs", patterns)
    assert checker.is_ignored_link("https://example.com/exact", patterns)
    assert not checker.is_ignored_link("https://example.com/other", patterns)


def test_external_link_checker_syntax_only_honors_ignore_file(tmp_path: Path) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[ignored](https://ignored.example.com/bad path)\n[checked](https://example.com/docs)\n"
    )
    ignore_file = tmp_path / ".external-links-ignore"
    ignore_file.write_text("# Intentional unstable test URL.\nhttps://ignored.example.com/*\n")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "syntax-checked 1 external HTTP(S) link(s); ignored 1" in result.stdout


def test_external_link_checker_verbose_mode_reports_ignored_links(tmp_path: Path) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[ignored](https://ignored.example.com/docs)\n[checked](https://example.com/docs)\n"
    )
    (tmp_path / ".external-links-ignore").write_text(
        "# Intentional unstable test URL.\nhttps://ignored.example.com/*\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
            "--verbose",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "checking" in result.stdout
    assert "https://example.com/docs" in result.stdout
    assert "ignored" in result.stdout
    assert "https://ignored.example.com/docs" in result.stdout
    assert "matched https://ignored.example.com/*" in result.stdout
    assert "ignore pattern https://ignored.example.com/* matches" in result.stdout


def test_external_link_checker_verbose_mode_reports_successful_checked_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    import sys

    checker_path = Path.cwd() / "scripts/check_external_links.py"
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[checked](https://example.com/docs)\n")

    result = subprocess.run(
        [
            sys.executable,
            str(checker_path),
            "--root",
            str(tmp_path),
            "--verbose",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Real network behavior varies; this test only requires successful checks to use
    # verbose-only per-link output in syntax-only mode, where success is deterministic.
    assert "ok " not in result.stdout

    syntax_result = subprocess.run(
        [
            sys.executable,
            str(checker_path),
            "--root",
            str(tmp_path),
            "--syntax-only",
            "--verbose",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "checking" in syntax_result.stdout
    assert "syntax-checked 1 external HTTP(S) link(s)" in syntax_result.stdout
    assert "ok " not in syntax_result.stdout


def test_external_link_checker_validates_ignore_pattern_reasons(tmp_path: Path) -> None:
    checker = load_external_link_checker_module()
    valid_ignore_file = tmp_path / "valid.ignore"
    valid_ignore_file.write_text(
        "# Vendor docs block automated HEAD/GET checks.\nhttps://vendor.example.com/*\n"
    )
    invalid_ignore_file = tmp_path / "invalid.ignore"
    invalid_ignore_file.write_text("https://vendor.example.com/*\n")

    assert checker.ignore_file_reason_errors(valid_ignore_file) == []
    assert checker.ignore_file_reason_errors(tmp_path / "missing.ignore") == []
    assert checker.ignore_file_reason_errors(invalid_ignore_file) == [
        f"{invalid_ignore_file}:1: ignore pattern must be preceded by a reason comment"
    ]


def test_external_link_checker_fails_for_unexplained_ignore_pattern(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[ignored](https://ignored.example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text("https://ignored.example.com/*\n")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ignore pattern must be preceded by a reason comment" in result.stderr


def test_external_link_checker_validates_ignore_pattern_url_shape(tmp_path: Path) -> None:
    checker = load_external_link_checker_module()
    invalid_ignore_file = tmp_path / "invalid-shape.ignore"
    invalid_ignore_file.write_text(
        "# Missing host.\n"
        "https:///missing-host/*\n"
        "# Unsupported scheme.\n"
        "ftp://example.com/*\n"
        "# Whitespace is not allowed.\n"
        "https://example.com/bad path/*\n"
    )

    assert checker.is_valid_external_http_pattern("https://example.com/*")
    assert checker.is_valid_external_http_pattern("http://example.com/path*")
    assert not checker.is_valid_external_http_pattern("https:///missing-host/*")
    assert not checker.is_valid_external_http_pattern("ftp://example.com/*")
    assert not checker.is_valid_external_http_pattern("https://example.com/bad path/*")
    assert checker.ignore_file_errors(invalid_ignore_file) == [
        f"{invalid_ignore_file}:2: ignore pattern must be an HTTP(S) URL pattern",
        f"{invalid_ignore_file}:4: ignore pattern must be an HTTP(S) URL pattern",
        f"{invalid_ignore_file}:6: ignore pattern must be an HTTP(S) URL pattern",
    ]


def test_external_link_checker_fails_for_invalid_ignore_pattern_shape(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[checked](https://example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text("# Unsupported scheme.\nftp://example.com/*\n")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ignore pattern must be an HTTP(S) URL pattern" in result.stderr


def test_external_link_checker_finds_unmatched_ignore_patterns() -> None:
    checker = load_external_link_checker_module()
    links_by_file = {
        Path("README.md"): [
            "https://example.com/docs",
            "https://vendor.example.com/reference/cache",
        ]
    }

    assert (
        checker.unmatched_ignore_patterns(
            ["https://example.com/*", "https://vendor.example.com/reference/*"],
            links_by_file,
        )
        == []
    )
    assert checker.unmatched_ignore_patterns(
        ["https://missing.example.com/*", "https://example.com/*"],
        links_by_file,
    ) == ["https://missing.example.com/*"]


def test_external_link_checker_allows_empty_or_comment_only_ignore_file(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[checked](https://example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text("# Template only.\n")

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "syntax-checked 1 external HTTP(S) link(s)" in result.stdout


def test_external_link_checker_fails_for_stale_ignore_pattern(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[checked](https://example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text(
        "# Former unstable vendor docs URL.\nhttps://missing.example.com/*\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ignore pattern does not match any current docs link" in result.stderr
    assert "https://missing.example.com/*" in result.stderr


def test_external_link_checker_can_allow_stale_ignore_patterns(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[checked](https://example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text(
        "# Staged vendor docs ignore for a nearby docs change.\nhttps://missing.example.com/*\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
            "--allow-stale-ignores",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "syntax-checked 1 external HTTP(S) link(s)" in result.stdout


def test_external_link_checker_json_output_is_quiet_for_release_automation(
    tmp_path: Path,
) -> None:
    import json
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[ignored](https://ignored.example.com/docs)\n[checked](https://example.com/docs)\n"
    )
    (tmp_path / ".external-links-ignore").write_text(
        "# Intentional unstable test URL.\nhttps://ignored.example.com/*\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
            "--verbose",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == {
        "checked": 1,
        "failures": [],
        "ignored": 1,
        "mode": "syntax-checked",
        "ok": True,
    }
    assert result.stderr == ""


def test_external_link_checker_fails_for_expired_ignore_pattern(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[ignored](https://ignored.example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text(
        "# Temporary vendor outage; expires: 2000-01-01\nhttps://ignored.example.com/*\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ignore pattern expired on 2000-01-01" in result.stderr


def test_external_link_checker_allows_future_ignore_expiration(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("[ignored](https://ignored.example.com/docs)\n")
    (tmp_path / ".external-links-ignore").write_text(
        "# Temporary vendor outage; expires: 2999-01-01\nhttps://ignored.example.com/*\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "scripts/check_external_links.py"),
            "--root",
            str(tmp_path),
            "--syntax-only",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ignored 1" in result.stdout


def test_retry_docs_include_idempotency_guidance() -> None:
    text = Path("docs/retry.md").read_text()

    for required in [
        "## Idempotency guidance",
        "idempotency key",
        "payments",
        "email sending",
        "duplicate attempts",
    ]:
        assert required in text


def test_rate_limit_docs_include_side_effect_and_distributed_caveats() -> None:
    text = Path("docs/rate_limit.md").read_text()

    for required in [
        "## Idempotency and side effects",
        "does not make an operation idempotent",
        "distributed system",
        "separate in-memory bucket",
        "retry-after",
    ]:
        assert required in text


def test_docs_example_link_labels_match_filenames() -> None:
    docs_index = Path("docs/index.md").read_text()
    example_links = re.findall(r"\[`([^`]+)`\]\((examples/[^)]+\.py)\)", docs_index)

    assert example_links
    for label, target in example_links:
        assert label == Path(target).name


def test_planning_docs_are_not_user_navigation_docs_by_default() -> None:
    planning_docs = [Path("GOAL.md"), Path("PLAN.md"), Path("TODO.md")]
    root_navigation_docs = {
        Path("README.md"),
        Path("CONTRIBUTING.md"),
        Path("RELEASE.md"),
    }

    for planning_doc in planning_docs:
        assert planning_doc not in root_navigation_docs
        assert "[Documentation Index](docs/index.md)" not in planning_doc.read_text()
        assert "[docs index](docs/index.md)" not in planning_doc.read_text()


def test_contributing_documents_planning_doc_navigation_boundary() -> None:
    contributing = Path("CONTRIBUTING.md").read_text()

    assert "planning/backlog files" in contributing
    assert "deliberately promoted to user-facing documentation" in contributing
    assert "not required to link the docs index" in contributing


def test_timeout_docs_explain_custom_exception_constructor_contract() -> None:
    text = Path("docs/timeout.md").read_text()

    for required in [
        "constructible with a single message string",
        "require additional",
        "constructor arguments are not supported",
    ]:
        assert required in text


def test_contributing_documents_full_gate_hatch_alias() -> None:
    text = Path("CONTRIBUTING.md").read_text()

    assert "hatch run full-gate" in text
    assert "dogfood" in text


def test_quality_gates_page_documents_full_gate_commands() -> None:
    text = Path("docs/quality_gates.md").read_text()

    for command in [
        "hatch run full-gate",
        "./scripts/docs-policy.sh",
        "ruff check .",
        "mypy",
        "python scripts/dogfood_external_project.py",
    ]:
        assert command in text


def test_docs_example_index_checker_is_in_docs_policy_script() -> None:
    script = Path("scripts/docs-policy.sh").read_text()

    assert "python scripts/check_docs_example_index.py" in script


def test_docs_example_index_checker_lists_all_examples() -> None:
    checker = Path("scripts/check_docs_example_index.py").read_text()

    assert "sorted(EXAMPLES_DIR.glob" in checker
    assert "__init__.py" in checker
