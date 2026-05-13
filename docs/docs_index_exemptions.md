# Docs index exemption registry

Most top-level Markdown files under `docs/` must be linked from `docs/index.md`. Intentional exceptions belong in `DOCS_INDEX_EXEMPTIONS` in `tests/docs_policy_helpers.py`, with a policy test proving each exempt file exists and is deliberately excluded.

Use an exemption only for files that would make the public documentation index worse, such as the index page itself or generated/internal policy scaffolding. Do not use exemptions to hide unfinished public docs; either finish the page, link it from the right section, or keep it out of `docs/` until it is ready.

When adding an exemption:

1. Add the path to `DOCS_INDEX_EXEMPTIONS`.
2. Add or update the reason in the relevant docs-maintenance note.
3. Run `./scripts/docs-policy.sh`.

This keeps the index from turning into either a junk drawer or a magician's cabinet. Both are bad, but only one wears a cape.
