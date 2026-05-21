# Writing Style Audit

Reviewed against the project documentation voice described in [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md).

Scope: all project Markdown documentation under the repository, excluding generated/cache directories. That is 37 files: root docs ([`README.md`](https://github.com/RusDavies/pydecorators/blob/master/README.md), [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md), [`RELEASE.md`](https://github.com/RusDavies/pydecorators/blob/master/RELEASE.md), [`CHANGELOG.md`](https://github.com/RusDavies/pydecorators/blob/master/CHANGELOG.md), [`GOAL.md`](https://github.com/RusDavies/pydecorators/blob/master/GOAL.md), [`PLAN.md`](https://github.com/RusDavies/pydecorators/blob/master/PLAN.md), [`DOGFOOD.md`](https://github.com/RusDavies/pydecorators/blob/master/DOGFOOD.md), [`TODO.md`](https://github.com/RusDavies/pydecorators/blob/master/TODO.md), PR template) plus the `docs/` tree.

## Overall verdict

The documentation is mostly aligned with the desired style.

It already avoids the worst AI/corporate sludge. I found no hits for the explicit banned phrases from the style guide, including `delve`, `unlock`, `leverage`, `seamless`, `transformative`, or the usual LinkedIn fog machine exhaust.

The project voice is strongest in the README and the major design docs. Phrases like "dependency shrubbery", "decorator soup is still soup", and "not a distributed cache and should not pretend to be one while wearing a fake moustache" are exactly the right kind of dry: useful first, mildly amused second.

The main weakness is not tone. It is density. Several docs are accurate but too reference-heavy. They describe behavior well, but they sometimes need sharper framing: why the distinction matters, what breaks when users ignore it, and what trade-off the project is choosing.

## Strong matches

- [`README.md`](https://github.com/RusDavies/pydecorators/blob/master/README.md)
  - Clear project positioning.
  - Practical examples.
  - Good warnings around pre-alpha status and decorator composition.
  - Voice is human without getting cute.

- [`docs/cache_result.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/cache_result.md)
  - Good boundary-setting: local process cache, not Redis in a trench coat.
  - Useful implementation detail without sounding academic.
  - Strong operational cautions around exception caching and invalidation.

- [`docs/disk_cache_backend.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md)
  - Best example of the intended voice in the docs.
  - Defines constraints clearly: local SQLite cache, not distributed infrastructure.
  - Explains practical failure modes: serialization, schema versioning, corruption, stale rows, and concurrency.

- [`docs/security_hardening.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/security_hardening.md)
  - Naturally fits the style guide because it talks in risks, failure modes, and consequences.
  - Good use of concrete controls rather than abstract safety language.

- [`GOAL.md`](https://github.com/RusDavies/pydecorators/blob/master/GOAL.md)
  - Good systems framing for scope, users, and non-goals.
  - The "swamp of cleverness" line is on-brand and useful.

## Main style gaps

### 1. Some docs are too mechanically complete

Affected files:

- [`docs/PUBLIC_API.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md)
- [`docs/API_REFERENCE.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/API_REFERENCE.md)
- [`docs/API_DESIGN.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/API_DESIGN.md)
- [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md)
- [`docs/release_note_template.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/release_note_template.md)

These are accurate, but they read like internal reference material. That is acceptable for some pages, but the style guide asks for practical consequence, not just classification.

Recommended fix: add a short opening paragraph to reference-heavy docs that answers:

- What decision does this document help the reader make?
- What mistake does it prevent?
- What compatibility or operational constraint is being protected?

Example direction:

> This policy exists to keep the library boring in the useful sense. If a name is public, users can build on it. If it is internal, we can still fix our own machinery without turning every refactor into a compatibility incident.

### 2. Several pages need stronger trade-off framing

Affected files:

- [`docs/timeout.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/timeout.md)
- [`docs/sync_timeout_decision.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/sync_timeout_decision.md)
- [`docs/rate_limit.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/rate_limit.md)
- [`docs/circuit_breaker.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/circuit_breaker.md)
- [`docs/redis_backend_design.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/redis_backend_design.md)
- [`docs/observability_integrations.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/observability_integrations.md)

These docs explain what the feature does, but some should more explicitly state what is being traded away.

Examples:

- Timeout docs should say more directly that async timeout is cooperative cancellation, not a magic thread-killing device.
- Rate limiting docs should distinguish fairness, throughput, latency, and caller experience.
- Circuit breaker docs should explain that the decorator protects dependencies and callers by failing fast, but can also hide recovery if thresholds are wrong.
- Redis backend design should be explicit about where Redis changes the operating model: shared state, network failure, expiry semantics, deployment burden, and observability.

### 3. Long Markdown lines hurt editability

The prose is often readable when rendered, but many files have very long source lines. That makes reviews noisier and future edits more annoying than they need to be. Humans edit diffs; machines merely endure them.

Most affected files by long non-table lines:

- [`docs/disk_cache_backend.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md)
- [`docs/cache_result.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/cache_result.md)
- [`docs/PUBLIC_API.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md)
- [`README.md`](https://github.com/RusDavies/pydecorators/blob/master/README.md)
- [`RELEASE.md`](https://github.com/RusDavies/pydecorators/blob/master/RELEASE.md)
- [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md)

Recommended fix: reflow prose in touched areas during future edits. Do not churn the entire repo only for wrapping unless there is already a docs cleanup branch.

### 4. A few terms are bland without context

I found only light cases, not serious offences. Words like `simple`, `flexible`, `clean`, and `production` appear occasionally. They are not banned, but the style guide says to make them earn their keep.

Recommended fix: when editing nearby text, replace vague praise with the actual property.

Examples:

- Instead of "simple", say "small enough to understand without reading the wrapper internals".
- Instead of "flexible", say which dimensions vary: key function, TTL, backend, exception policy, hook behavior.
- Instead of "production", say what condition is production-relevant: concurrency, observability, failure isolation, compatibility, or release safety.

## File-by-file notes

### Root docs

- [`README.md`](https://github.com/RusDavies/pydecorators/blob/master/README.md): Strong. Keep as the voice anchor for the project. Minor future improvement: add one sharper paragraph explaining the library's non-goal: it is not a framework and should not grow tentacles.
- [`GOAL.md`](https://github.com/RusDavies/pydecorators/blob/master/GOAL.md): Strong. Good project framing. Could be tightened after release scope settles.
- [`PLAN.md`](https://github.com/RusDavies/pydecorators/blob/master/PLAN.md): Serviceable project-plan prose. It is allowed to be plain. No major style concern.
- [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md): Useful, but could use more direct "why this matters" language in the quality gate and public API sections.
- [`RELEASE.md`](https://github.com/RusDavies/pydecorators/blob/master/RELEASE.md): Complete, but dense. Good candidate for reflow and sharper consequence-oriented wording before first release.
- [`DOGFOOD.md`](https://github.com/RusDavies/pydecorators/blob/master/DOGFOOD.md): Good. Practical and candid.
- [`CHANGELOG.md`](https://github.com/RusDavies/pydecorators/blob/master/CHANGELOG.md): Fine. Changelog prose should be factual and boring; this is one place where boring is not a moral failure.
- [`TODO.md`](https://github.com/RusDavies/pydecorators/blob/master/TODO.md): Backlog format is fine. Do not over-style it.
- [`.github/pull_request_template.md`](https://github.com/RusDavies/pydecorators/blob/master/.github/pull_request_template.md): Fine. Templates should be direct, not literary.

### `docs/` tree

- [`docs/index.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/index.md): Accurate navigation. Add [`writing_style_audit.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/writing_style_audit.md) and keep descriptions crisp.
- [`docs/API_REFERENCE.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/API_REFERENCE.md): Accurate, but list-heavy. Add more reader-orientation at the top.
- [`docs/PUBLIC_API.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md): Important policy. Needs the strongest practical framing because compatibility policy is where future maintainers accidentally create archaeology.
- [`docs/API_DESIGN.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/API_DESIGN.md): Useful, but could explain the trade-off between decorator ergonomics and predictable typing more directly.
- [`docs/composition.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/composition.md): Good practical guidance. Could add one or two failure examples for bad decorator ordering.
- [`docs/exceptions.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/exceptions.md): Good structure. Could add a short "how to catch these without making a mess" section.
- [`docs/cache_result.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/cache_result.md): Strong. Keep the tone.
- [`docs/disk_cache_backend.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md): Strong but long. Reflow and possibly split later if it keeps growing.
- [`docs/redis_backend_design.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/redis_backend_design.md): Needs more operating-model language. Redis is not just a different storage bucket; it changes failure modes.
- [`docs/security_hardening.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/security_hardening.md): Strong. Keep consequence-first wording.
- [`docs/quality_gates.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/quality_gates.md): Good. Could be more explicit about which gates protect users versus maintainers.
- Per-decorator docs (`deprecated`, `retry`, `rate_limit`, `timeout`, `log_calls`, `measure_time`, `validate_types`, `require_env`, `circuit_breaker`): generally clear. Best future improvement is more "what goes wrong if you misuse this" framing.
- Planning/policy docs (`docs_site_plan`, `future_extension_decisions`, `markdown_anchor_policy`, `docs_index_exemptions`, `sync_timeout_decision`, `release_note_template`): acceptable as internal docs. Keep them concise and do not try to make them charming. Charm in policy docs is how committees happen.

## Recommended backlog

1. Add a short project documentation style note to [`CONTRIBUTING.md`](https://github.com/RusDavies/pydecorators/blob/master/CONTRIBUTING.md), pointing contributors at the project writing-style guidance and summarizing the local expectations.
2. Tighten the opening sections of [`PUBLIC_API.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/PUBLIC_API.md), [`API_REFERENCE.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/API_REFERENCE.md), and [`API_DESIGN.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/API_DESIGN.md) so they explain the practical decision each document supports.
3. Add failure-mode examples to [`composition.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/composition.md), [`timeout.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/timeout.md), [`rate_limit.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/rate_limit.md), and [`circuit_breaker.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/circuit_breaker.md).
4. Reflow long prose lines opportunistically when editing docs; avoid a noisy repo-wide wrap-only change unless the team explicitly wants it.
5. Revisit [`redis_backend_design.md`](https://github.com/RusDavies/pydecorators/blob/master/docs/redis_backend_design.md) with an operating-model pass before implementing Redis support.

## Bottom line

The docs are not beige. Good start.

The next improvement is to make the reference-heavy pages less like inventories and more like technical guidance: define the boundary, name the trade-off, and land the operational consequence. That is the Russ style, minus the consultant fog and plus a small amount of adult supervision.
