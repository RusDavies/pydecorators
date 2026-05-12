"""Check that docs/index.md lists executable example files in generated order."""

from __future__ import annotations

from pathlib import Path

EXAMPLES_DIR = Path("docs/examples")
DOCS_INDEX = Path("docs/index.md")
START = "Executable documentation examples live under [`examples/`](examples/):\n\n"
END = "\nThese examples are exercised by the test suite"


def example_lines() -> list[str]:
    return [
        f"- [`{path.name}`](examples/{path.name})"
        for path in sorted(EXAMPLES_DIR.glob("*.py"))
        if path.name != "__init__.py"
    ]


def expected_block() -> str:
    return START + "\n".join(example_lines()) + "\n"


def current_block(text: str) -> str:
    start = text.index(START)
    end = text.index(END, start)
    return text[start:end]


def main() -> int:
    text = DOCS_INDEX.read_text()
    expected = expected_block()
    actual = current_block(text)
    if actual != expected:
        print("docs/index.md executable examples are out of date")
        print("Expected block:")
        print(expected)
        return 1
    print(f"docs/index.md lists {len(example_lines())} executable example files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
