# Documentation Site Plan

The first public documentation target is the repository README plus linked Markdown docs. A generated documentation site can wait until the package is closer to publish/release traffic.

## Current posture

- Keep docs as plain Markdown committed under `docs/`.
- Keep [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md) as the source-of-truth navigation page.
- Keep executable examples under `docs/examples/` and require `scripts/check_docs_example_index.py` to catch index drift.
- Keep external link checks opt-in/local so contributors are not blocked by transient network failures.

## Site generator decision

Do not add MkDocs, Sphinx, Astro, or another site generator yet. A site generator adds dependency, theme, deploy, and URL-policy choices before the project has enough external usage to justify them.

When the documentation site becomes worthwhile, prefer a small static generator with:

- Markdown-first authoring
- stable heading anchors
- local preview command
- no analytics by default
- deployment that can run from GitHub Actions without secrets for preview builds

## Minimum launch checklist

Before enabling a docs site, add:

- a site config file
- a local preview command in [`docs/quality_gates.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/quality_gates.md) or [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md)
- link-check coverage for generated URLs or equivalent source Markdown checks
- a release-docs note describing which URL is canonical
- a redirect/anchor policy for public pages

Until then, the documentation site backlog item is intentionally satisfied by this plan rather than by dragging in a full publishing stack prematurely. Radical restraint; try not to faint.
