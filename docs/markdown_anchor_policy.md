# Markdown anchor policy

The docs-policy tests use a small GitHub-style heading anchor helper when they verify links between Markdown files. The helper lowercases headings, removes punctuation, replaces whitespace with hyphens, collapses duplicate hyphens, and trims edge hyphens after non-ASCII or symbol-heavy text is stripped.

This is intentionally a compatibility check for the Markdown currently used in this repository, not a promise to implement every renderer's anchor algorithm. Keep headings simple when they need stable links:

- prefer plain ASCII words for public anchors;
- avoid duplicate headings in one file;
- avoid relying on punctuation-only differences;
- add tests before introducing reference-style links, duplicate-heading suffixes, or renderer-specific anchor behavior.

If the documentation moves to a generated site with a different anchor algorithm, update `tests/docs_policy_helpers.py` and this page in the same change. Markdown: now with just enough policy to keep future-us from inventing archaeology as a CI strategy.
