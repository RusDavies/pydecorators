# Security Audit — 2026-05-21

Scope: local security audit of `projects/python-decorators` / `blakemere-wraptools` at commit
`9288399edf93738a60b0fd1e92d456deadbb0a28`.

Evidence store: `.openclaw-security-audit/audit.sqlite` with the generated Markdown report
inside the same ignored audit-artifact directory.

## Method

- Initialized the OpenClaw security-audit evidence database.
- Built repository inventory: 142 files, Python package manifest in `pyproject.toml`.
- Extracted symbols: 511 symbols from 57 scanned source/test files.
- Ran Semgrep `p/python`: 151 rules over 26 tracked Python files, 1 finding.
- Ran `ruff check .`: passed.
- Ran `mypy`: passed.
- Manually reviewed the highest-risk PyDecorators surfaces:
  - persistent cache serialization and SQLite handling;
  - optional Redis cache namespace handling;
  - logging redaction / argument-result logging;
  - environment-variable checks;
  - GitHub Actions CI and trusted publishing workflow;
  - package metadata and dependency declarations.

Unavailable local tools during this run: `bandit`, `pip-audit`, `safety`, `osv-scanner`,
`gitleaks`, and `trufflehog` were not installed. Runtime dependencies are empty; optional
runtime dependency is `redis>=5`.

## Summary

No P0/P1 release-blocking issue was found.

Findings:

- P2: Redis cache `key_prefix` accepts Redis glob metacharacters that are later used in
  `SCAN` patterns.
- P4: local coverage-summary helper uses `xml.etree.ElementTree.parse` on a caller-supplied
  XML path; normal CI input is locally generated, so this is hardening noise rather than a
  package-runtime vulnerability.

## Finding P2 — Redis key-prefix glob metacharacters can widen namespace scans

Status: remediated in branch work after the audit
Priority: P2
Confidence: high
Affected file: `src/pydecorators/redis_backend.py`

### Evidence

`RedisCacheBackend.__init__` validates `key_prefix` only for non-empty and no whitespace:

- `src/pydecorators/redis_backend.py:61-64`

The same prefix is used directly in Redis glob-style scan patterns:

- `src/pydecorators/redis_backend.py:108-115` in `clear()`
- `src/pydecorators/redis_backend.py:120-125` in `info()`
- `src/pydecorators/redis_backend.py:162-166` in `_evict_if_needed()`

The concrete pattern is equivalent to:

```python
self._scan_keys(f"{self._key_prefix}:entry:*")
```

Redis `SCAN MATCH` uses glob-style matching, so prefixes containing `*`, `?`, or character
classes can match outside the intended namespace.

Local fake-Redis proof:

```text
before ['safe:stats:hits', 'tenant-a:entry:abc', 'tenant-b:entry:def']
after ['safe:stats:hits']
```

That PoC used `RedisCacheBackend(client=fake, key_prefix='*')` and then called `clear()`.
Both tenant entry keys were deleted because the scan pattern became `*:entry:*`.

### Reachability

The affected constructor is public API. The issue matters when an application derives
`key_prefix` from tenant/user input, untrusted configuration, or any value not fully controlled
by the application owner.

If `key_prefix` is a fixed application constant, this is not exploitable by a remote attacker.

### Impact

- Cross-namespace cache deletion via `clear()`.
- Cross-namespace cache counting via `info()`.
- Possible cross-namespace eviction when `maxsize` is enabled.

This is cache integrity/availability impact, not direct code execution or secret disclosure.

### Recommendation

Reject Redis glob metacharacters in `key_prefix`, or encode/hash the logical namespace before
using it in Redis key names and scan patterns. Add regression tests for at least `*`, `?`, `[`,
and `]`, and document that prefixes are literal namespace identifiers.

### Remediation

Follow-up branch work rejects `*`, `?`, `[`, and `]` in `RedisCacheBackend.key_prefix`, adds
regression coverage for all four metacharacters, and documents the literal-prefix rule in the
Redis backend design notes.

## Finding P4 — local coverage XML parser hardening

Status: `unreachable_current_config`
Priority: P4
Confidence: medium
Affected file: `scripts/coverage_summary.py`

### Evidence

Semgrep `p/python` flagged:

- `scripts/coverage_summary.py:12`: `ET.parse(path).getroot()`

`coverage_xml` is a local CLI argument defaulting to `coverage.xml`. In normal CI use, this
file is generated locally by pytest coverage during the same job.

### Reachability

No package runtime surface reaches this script. A maintainer would have to manually run it on
untrusted XML for the concern to matter.

### Recommendation

Either leave as accepted local-tool risk, or switch to `defusedxml` if a dev dependency is
acceptable. Given the current tiny helper and trusted CI input, this should not block release.

## Non-findings / guarded areas

- `PickleCacheSerializer` and `DiskCacheBackend` do deserialize pickle payloads, but public docs
  and security guidance clearly state that cache files are trusted local files only and must not
  come from untrusted sources.
- `DiskCacheBackend.inspect_entries()` avoids deserializing pickle/binary payloads for previews;
  preview output is bounded and redactor failures suppress the preview.
- `@log_calls` defaults to metadata-only logging. Argument/result logging is opt-in, and docs
  warn that redaction is shallow and caller-owned.
- `@validate_types` docs explicitly say it is not a schema validator or security boundary.
- Release workflow uses trusted publishing with minimal `contents: read` and publish-job
  `id-token: write`, scoped to protected GitHub environments.

## Follow-up TODOs added

- Reject or encode Redis glob metacharacters in `RedisCacheBackend.key_prefix` before using it in
  scan/delete/eviction patterns.
- Decide whether `scripts/coverage_summary.py` should use `defusedxml` or keep the Semgrep finding
  as accepted local-tool risk.
