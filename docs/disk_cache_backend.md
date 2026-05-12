# `DiskCacheBackend` Design

`DiskCacheBackend` should provide persistent local cache storage for `@cache_result` using SQLite from the Python standard library.

The goal is a durable cache for CLIs, scripts, local tools, and single-host services. It is not a distributed cache and should not pretend to be one while wearing a fake moustache.

## Recommended public shape

```python
from pathlib import Path
from useful_decorators import DiskCacheBackend, JsonCacheSerializer, PickleCacheSerializer

backend = DiskCacheBackend(
    path=Path(".cache/useful-decorators.sqlite3"),
    ttl=3600,
    maxsize=10_000,
    serializer=PickleCacheSerializer(),
)

@cache_result(backend=backend, namespace="users")
def load_user(user_id: str) -> User:
    ...
```

## Constructor parameters

Planned signature:

```python
class DiskCacheBackend:
    def __init__(
        self,
        path: str | Path,
        *,
        ttl: float | None = None,
        maxsize: int | None = 128,
        refresh_ttl_on_hit: bool = False,
        serializer: CacheSerializer | None = None,
        on_drop: Callable[[DiskCacheDropEvent], object] | None = None,
        clock: Clock | None = None,
        busy_timeout_ms: int = 5_000,
        wal: bool = True,
    ) -> None: ...
```

- `path`: SQLite database path.
- `ttl`: optional entry lifetime in seconds.
- `maxsize`: optional maximum entry count.
- `refresh_ttl_on_hit`: when `True`, hits extend entry expiry to `clock() + ttl`; default `False` keeps fixed write-time expiry.
- `serializer`: payload serializer; defaults to `PickleCacheSerializer`.
- `on_drop`: optional diagnostic hook called with `DiskCacheDropEvent` when a stored row is dropped during lookup because of a serializer content-type mismatch or payload deserialization failure.
- `clock`: injectable monotonic-ish clock for deterministic tests.
- `busy_timeout_ms`: SQLite busy timeout in milliseconds; defaults to `5000`.
- `wal`: whether to request SQLite WAL journal mode; defaults to `True`.

## SQLite schema

Use one table for entries and one table for stats.

```sql
CREATE TABLE IF NOT EXISTS cache_entries (
    key BLOB PRIMARY KEY,
    payload BLOB NOT NULL,
    is_exception INTEGER NOT NULL,
    expires_at REAL,
    last_accessed REAL NOT NULL,
    created_at REAL NOT NULL,
    serializer_content_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cache_stats (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    hits INTEGER NOT NULL,
    misses INTEGER NOT NULL
);
```

Initialize stats with `(id=1, hits=0, misses=0)`.

## Key serialization

Keys should be serialized separately from payloads.

Recommended first implementation:

- Use `PickleCacheSerializer` internally for generated cache keys.
- Store serialized keys as the SQLite `BLOB PRIMARY KEY`.
- Keep `CacheKeyError` for unhashable key failures before serialization.

Reason: generated keys are Python tuples containing marker objects, argument values, and possibly types. Pickle preserves those reliably enough for local trusted disk caches.

## Payload serialization

Payloads use the configured `CacheSerializer`. The built-in serializers are:

- `PickleCacheSerializer`: the default Python-object serializer for trusted local cache files.
- `JsonCacheSerializer`: UTF-8 JSON for simple JSON-compatible values when payloads should be easier to inspect or consume from other languages. It does not preserve arbitrary Python object types.

- Successful values store `is_exception=0`.
- Cached exceptions store `is_exception=1`.
- Store `serializer_content_type` with each row so future migrations or debugging can detect format mismatches.

## TTL behavior

- `expires_at` is computed at write time as `clock() + ttl`.
- `None` means no TTL expiry.
- Reads treat expired rows as misses and delete the expired row.
- `info()` prunes expired rows before reporting `currsize`.
- Cache hits refresh TTL only when `refresh_ttl_on_hit=True`; the default fixed TTL does not refresh on hit.

## Sliding TTL refresh

`DiskCacheBackend(refresh_ttl_on_hit=True)` enables sliding TTL for disk-backed entries. On a valid hit, the backend updates both `last_accessed` and `expires_at`; the refreshed expiry is `clock() + ttl`.

Default behavior remains fixed TTL: entries expire based on their original write time even if they are read repeatedly. This is easier to reason about for release/build caches. Sliding TTL is useful for local service caches where hot entries should stay warm.

If `ttl=None`, `refresh_ttl_on_hit=True` has no practical effect because entries have no expiry to refresh.

## LRU eviction

Use `last_accessed` for LRU behavior.

- On hit, update `last_accessed`.
- On write, set `created_at` and `last_accessed` to `clock()`.
- When `maxsize` is exceeded, delete the oldest rows by `last_accessed`.

Suggested eviction query:

```sql
DELETE FROM cache_entries
WHERE key IN (
    SELECT key FROM cache_entries
    ORDER BY last_accessed ASC
    LIMIT ?
);
```

## Statistics

Stats should behave like `MemoryCacheBackend`:

- `get()` increments hits on valid row hits.
- `get()` increments misses on absent or expired rows.
- `clear()` deletes all entries and resets hits/misses.
- `info()` returns `CacheInfo(hits, misses, maxsize, currsize)`.

## Transactions and connections

- Use `sqlite3` from the standard library.
- Open a connection per backend instance.
- Use `check_same_thread=False` plus an internal `RLock`, or keep default thread checks and document one-backend-per-thread.
- Recommendation: use `check_same_thread=False` with `RLock` so behavior matches memory backend thread-safety expectations.
- Use explicit transactions for writes.

## Trust boundary warning

The default `PickleCacheSerializer` is only safe for trusted local cache files. Loading pickle data from an attacker-controlled SQLite file can execute code.

Docs for `DiskCacheBackend` must warn:

- Do not use cache files from untrusted sources.
- Do not place cache DBs in world-writable directories.
- Prefer `JsonCacheSerializer` for simple JSON-compatible payloads that should avoid pickle or be easier to inspect from other languages.

## JSON payload serializer

Use `JsonCacheSerializer` when cached values are JSON-compatible and do not need Python object identity or custom classes preserved:

```python
from pathlib import Path

from useful_decorators import DiskCacheBackend, JsonCacheSerializer, cache_result

backend = DiskCacheBackend(
    Path(".cache/useful-decorators.sqlite3"),
    serializer=JsonCacheSerializer(),
)


@cache_result(backend=backend, namespace="users-json:v1")
def load_user_profile(user_id: str) -> dict[str, object]:
    return {"id": user_id, "display_name": "Ada"}
```

JSON serialization is stricter than pickle. It supports ordinary JSON values (`None`, booleans, finite numbers, strings, lists, and dictionaries with string keys), rejects non-finite numbers such as `NaN`, and does not preserve tuples, exceptions, custom classes, bytes, datetimes, or other Python-specific objects. Avoid `cache_exceptions=True` with `JsonCacheSerializer` unless the exception payloads are converted by a custom wrapper/serializer first.

Changing between `PickleCacheSerializer` and `JsonCacheSerializer` changes `serializer_content_type`; existing rows written with the old content type are treated as misses and removed rather than being deserialized with the wrong serializer.

## Inspecting JSON cache rows with SQLite

When `DiskCacheBackend` uses `JsonCacheSerializer`, payload bytes are UTF-8 JSON and can be inspected with ordinary SQLite tools. This is useful for debugging local caches or confirming what a simple cross-language consumer would see.

The cache key is still an internal pickle-serialized Python key, so inspect payload columns for debugging rather than treating the SQLite file as a stable application database. Cache rows are disposable implementation details, not a public storage schema with a tiny hat.

Example SQL:

```sql
SELECT payload, serializer_content_type
FROM cache_entries
LIMIT 1;
```

Executable example: `docs/examples/disk_cache_backend_examples.py::inspect_json_cache_row_example` writes a JSON payload with `JsonCacheSerializer`, opens the SQLite file directly, reads `payload` and `serializer_content_type`, and verifies the stored payload is ordinary compact JSON such as `{"id":"user-123","active":true}` with content type `application/json`.

## SQLite column stability for debugging

Direct SQLite inspection is supported only as a debugging aid. The durable public API remains `DiskCacheBackend`, `CacheBackend`, `CacheInfo`, serializers, and documented decorator behavior. Do not treat the SQLite file as an application database, replication source, or migration target unless a future release explicitly promotes that contract.

Debugging-friendly columns:

- `payload`: useful to inspect when the active serializer is human-readable, such as `JsonCacheSerializer` or a custom JSON serializer. The meaning belongs to the serializer, not SQLite.
- `serializer_content_type`: useful to confirm which serializer family wrote a row and why a lookup may drop an incompatible row as a miss.
- `is_exception`: useful to distinguish cached return values from cached exceptions.
- `created_at`, `last_accessed`, and `expires_at`: useful for rough TTL/LRU debugging. Treat values as backend timestamps, not externally stable audit timestamps.

Internal implementation details:

- `key`: an internal serialized cache key. Its bytes depend on Python values, decorator key policy, namespace, `typed=True`, and implementation details. Do not parse it or use it as an external identifier.
- Table names, indexes, PRAGMAs, statistics storage, eviction queries, and exact timestamp update timing are internal unless specifically documented as public API.
- The shape of `cache_stats` is internal. Use `backend.info()` or decorated function `cache_info()` for supported hit/miss/current-size reporting.

Safe rule: inspect `payload` and `serializer_content_type` to answer “what did this local cache row store?”, but use backend APIs to mutate, clear, count, or rely on behavior. If tooling needs more stable inspection guarantees later, add an explicit API instead of scraping private organs.

## Supported cache-inspection API design

If users need stable tooling beyond ad hoc SQLite debugging, add an explicit inspection API instead of promoting direct table scraping. The API should expose cache diagnostics without making SQLite layout, serialized keys, or private timestamp mechanics part of the public contract.

Tentative public shape:

```python
@dataclass(frozen=True)
class DiskCacheInspectionEntry:
    is_exception: bool
    serializer_content_type: str
    payload_preview: str | None
    payload_size_bytes: int
    created_at: float
    last_accessed: float
    expires_at: float | None

@dataclass(frozen=True)
class DiskCacheInspectionReport:
    entries: tuple[DiskCacheInspectionEntry, ...]
    total_entries: int
    truncated: bool

report = backend.inspect_entries(limit=100, include_payload_preview=True)
```

Design constraints:

- The method should be read-only. Mutation belongs to `clear()`, `cache_clear()`, and future `maintain()`/repair-style APIs.
- It should not expose serialized `key` bytes by default. If key diagnostics are needed later, expose a redacted digest such as `key_sha256`, not a parseable implementation artifact.
- Payload previews should be best-effort and bounded. For JSON-like serializers, previews may decode UTF-8 and truncate safely. For pickle or unknown binary serializers, previews should default to `None` or a small diagnostic marker rather than deserializing arbitrary objects.
- It should report serializer content type and payload byte size without requiring payload deserialization.
- It should avoid promising exact LRU/TTL timing semantics beyond “these are the backend’s current stored timestamps.”
- It should have explicit `limit`/pagination behavior so accidental inspection does not scan huge cache files by default.
- It should return structured data suitable for a future CLI, not preformatted log text.

## Bounded payload preview policy design

Any future inspection API that exposes payload previews must be deliberately boring and safe. Previewing cache rows is for operator/debugging visibility, not for reconstructing cached values or bypassing serializer boundaries.

Proposed default policy:

- `include_payload_preview=False` by default for the first public inspection API. Callers must opt in.
- `payload_preview_max_bytes=256` by default, with a documented upper bound such as `4096` bytes.
- Truncation should happen by bytes before display formatting, and the result should include `payload_preview_truncated: bool` so callers do not mistake previews for complete payloads.
- UTF-8 JSON serializers may decode previews with `errors="replace"` after byte truncation. Invalid UTF-8 should never fail inspection.
- Binary, pickle, and unknown serializers should not be deserialized for previews. They should return `payload_preview=None` plus payload size/content-type metadata, or a small marker such as `<binary payload: 128 bytes>`.
- Pickle previews must never call `pickle.loads()`. The whole point is to avoid accidentally turning a diagnostic endpoint into a haunted object launcher.
- Previews should not include serialized cache keys. If key correlation is needed later, use a redacted digest such as `key_sha256`.
- Preview generation should be side-effect free and should not update `last_accessed`, hits, misses, TTL, or LRU state.
- Preview output should be documented as diagnostic-only and excluded from compatibility promises about exact formatting.

## Payload preview redaction expectations

Payload previews can expose cached return values, and cached return values may contain secrets, personal data, tokens, credentials, customer records, or proprietary content. Any future inspection API must treat previews as sensitive diagnostic output, not harmless metadata.

Redaction posture:

- Previews should be opt-in at the API call site and clearly documented as potentially sensitive.
- The library should not promise automatic secret detection. Generic redaction misses too much and creates fake safety.
- If redaction support is added, it should be explicit and caller-controlled, such as a `preview_redactor` callable or named redaction policy.
- Built-in redaction, if any, should be conservative and limited to obvious JSON object keys such as `password`, `secret`, `token`, `api_key`, `authorization`, and `cookie`. It should never be the only safety boundary.
- Redaction should happen after bounded decoding/truncation policy is applied, and should preserve the `payload_preview_truncated` signal.
- Inspection output should not be logged automatically by the library. Callers own where diagnostic reports go.
- Documentation should warn against enabling previews in shared logs, support bundles, CI artifacts, public bug reports, screenshots, or chat pastebins unless the payload domain is known safe. Yes, this includes pastebins. Especially pastebins.

## No-preview support bundle and CI mode

If inspection tooling is added, it should have a safe mode intended for support bundles, CI artifacts, issue templates, and automated diagnostics. That mode should include structural cache metadata while excluding payload previews entirely.

Tentative call shape:

```python
report = backend.inspect_entries(
    include_payload_preview=False,
    preview_redactor=None,
)
```

Safe-mode expectations:

- `include_payload_preview=False` should be the default and the recommended setting for support bundles, CI artifacts, public issues, screenshots, chat transcripts, and automated diagnostic uploads.
- Safe-mode reports may include counts, serializer content types, payload byte sizes, exception flags, expiry presence, and truncation/report pagination metadata.
- Safe-mode reports must not include payload preview text, raw payload bytes, serialized cache keys, or deserialized values.
- Safe-mode should not invoke `preview_redactor`; there is no preview to redact.
- Documentation should describe safe-mode output as lower-risk, not risk-free. Serializer content types, row counts, and payload sizes can still reveal application behavior. Tiny metadata can still wear a trench coat.
- Any future CLI should use safe mode by default and require an explicit flag such as `--include-payload-preview` before printing previews.

## Inspection CLI safe default design

If a disk-cache inspection CLI is added, its default output should be aggregate-only and no-preview. Users should have to make an explicit, noisy choice before printing row-level metadata or payload previews.

Tentative command posture:

```bash
python -m useful_decorators inspect-cache path/to/cache.sqlite3
python -m useful_decorators inspect-cache path/to/cache.sqlite3 --rows --no-payload-preview
python -m useful_decorators inspect-cache path/to/cache.sqlite3 --rows --include-payload-preview
```

CLI design constraints:

- Default command output should use the aggregate-only report.
- Row-level output should require an explicit flag such as `--rows`.
- Payload previews should require a second explicit flag such as `--include-payload-preview`.
- `--include-payload-preview` should print a warning unless a future `--quiet-sensitive-warning`/machine-readable mode has a documented replacement warning channel.
- JSON output should preserve the same safe defaults as text output. Machine-readable does not mean less sensitive; it just means easier to leak at scale.
- CLI help text should label row-level output and previews as potentially sensitive.
- The CLI should never mutate cache stats, TTL, LRU state, or maintenance state during inspection.

Pre-implementation tests should cover default aggregate/no-preview output, row output requiring `--rows`, preview output requiring `--include-payload-preview`, sensitivity warnings, JSON safe defaults, and no mutation during CLI inspection.

## Inspection sensitivity-warning design

Future inspection CLI/support-bundle tooling should warn users before producing diagnostic output that may be shared outside the local machine. The warning is not decoration; it is a guardrail against treating cache diagnostics as harmless build logs.

Warning expectations:

- Text CLI output should include a concise sensitivity warning by default for support-bundle and row-level inspection commands.
- JSON output should include a machine-readable warning field, such as `sensitivity_warning`, unless a documented envelope already carries equivalent classification metadata.
- Preview-enabled output should use stronger wording than aggregate/no-preview output.
- Quiet/scripted modes should require an explicit flag and should document where the warning is available instead, such as command help, schema docs, or wrapper tooling.
- Warnings should mention that metadata can reveal behavior even without payload previews.
- Warnings should not claim that redaction or no-preview mode makes output safe for public posting.

Pre-implementation tests should cover text warnings, JSON warning fields, stronger preview warnings, quiet-mode documentation, and absence of “safe for public sharing” language.

## Support-bundle metadata sensitivity

No-preview safe mode removes payload text, but it does not make inspection output public-safe by magic. Metadata can still reveal how an application behaves, what it caches, how often entries are reused, and whether errors or specific serializer families are present. Treat support-bundle inspection reports as potentially sensitive operational diagnostics.

Metadata that may reveal information:

- row counts can reveal feature usage, tenant/customer volume, or whether a workflow has run
- serializer content types can reveal implementation choices or payload classes
- payload byte sizes can reveal approximate record sizes, document sizes, or response-shape changes
- exception flags can reveal failing workflows or error-prone data paths
- expiry presence and timestamp patterns can reveal cache policy, workload timing, or recent activity
- pagination/truncation metadata can reveal cache scale even without payload previews

Support-bundle guidance:

- Prefer aggregate summaries over per-row metadata when broad sharing is enough.
- Share per-row no-preview reports only with trusted support/debugging recipients.
- Avoid attaching inspection reports to public issues unless the project owner has reviewed them.
- Document retention expectations for generated support bundles; caches are disposable, but reports can outlive the original cache file in places with worse access control.
- If a future CLI generates support bundles, it should label reports as potentially sensitive and default to aggregate/no-preview output.

## Aggregate-only inspection report design

If support-bundle tooling is added, start with an aggregate-only report before exposing per-row inspection data. Aggregate reports should answer “is the cache broadly healthy?” without listing individual cached objects.

Tentative aggregate shape:

```python
@dataclass(frozen=True)
class DiskCacheAggregateInspectionReport:
    total_entries: int
    value_entries: int
    exception_entries: int
    expired_entries: int
    serializer_content_types: Mapping[str, int]
    total_payload_bytes: int
    largest_payload_bytes: int | None
    earliest_created_at: float | None
    latest_created_at: float | None
    earliest_expires_at: float | None
    latest_expires_at: float | None
    report_truncated: bool
```

Design constraints:

- Aggregate reports should not include payload previews, raw payload bytes, deserialized values, serialized keys, key digests, or per-row timestamps.
- Content types should be counted by value, not listed alongside row identifiers.
- Payload sizes should be aggregated; the largest payload size is useful, but per-row sizes should stay out of broad support reports.
- Timestamp ranges should be coarse diagnostics, not audit logs.
- If the cache is too large to scan under a configured limit, `report_truncated=True` should make partial summaries obvious.
- Aggregate inspection should be read-only and should not update hits, misses, TTL, LRU, or `last_accessed`.
- Any future CLI support-bundle command should prefer this aggregate report by default.

Pre-implementation tests should cover aggregate reports excluding per-row data, preserving safe-mode no-preview behavior, surfacing truncation, and not mutating cache stats or recency state.

## Inspection report retention and deletion guidance

Generated inspection reports can outlive the cache files they summarize. A disposable local cache may become a durable artifact once copied into CI logs, issue attachments, chat transcripts, ticket systems, or support bundles. Treat generated reports as artifacts with their own retention policy.

Retention guidance:

- Prefer generating reports into caller-controlled paths, not hidden library-managed locations.
- Support-bundle tooling should document where reports are written and when they should be deleted.
- CI examples should avoid uploading inspection reports by default; if uploaded, retention should be short and access-controlled.
- Support workflows should delete local report files after transfer or after the debugging window closes.
- Reports should include creation time and safe-mode/preview-mode metadata so stale artifacts are easier to identify.
- Preview-enabled reports should be treated like sensitive data exports and should have stricter retention than aggregate/no-preview reports.
- The library should not silently phone home, upload, or retain inspection reports. External transfer remains the caller’s responsibility.

Pre-implementation tests should cover docs/examples that avoid automatic uploads, label report sensitivity, and show caller-owned output paths rather than hidden default report directories.

Pre-implementation tests should cover documentation and examples that label no-preview reports as lower-risk but still sensitive. If a future CLI/support-bundle command is added, tests should assert its default output excludes previews and includes a sensitivity warning.

Pre-implementation tests should cover:

- support/CI safe mode omits preview fields or sets them to `None`
- safe mode never calls caller-provided redactors
- safe mode includes enough non-payload metadata for useful diagnostics
- future CLI/default examples do not enable previews by default
- docs warn that metadata is lower-risk but not automatically non-sensitive

## `preview_redactor` callback design

If payload previews become part of `DiskCacheBackend.inspect_entries()`, redaction should be caller-owned and explicit. A callback gives applications a place to apply domain-specific policy without pretending the library can magically recognize every secret shaped like a cursed potato.

Tentative callback shape:

```python
@dataclass(frozen=True)
class DiskCachePreviewContext:
    serializer_content_type: str
    payload_size_bytes: int
    payload_preview_truncated: bool
    is_exception: bool

PreviewRedactor = Callable[[str, DiskCachePreviewContext], str | None]

report = backend.inspect_entries(
    include_payload_preview=True,
    preview_redactor=redact_preview,
)
```

Callback semantics:

- The callback receives the already bounded/decoded preview string, never raw payload bytes.
- Returning a string uses that value as the preview.
- Returning `None` suppresses the preview for that row.
- The callback receives metadata only; it should not receive serialized keys.
- The callback should run after truncation and basic decoding so it cannot accidentally request unbounded payload material.
- Redaction must preserve separate metadata such as `payload_preview_truncated`, `payload_size_bytes`, and `serializer_content_type`.
- If the callback raises, the safe default should be to suppress that row preview and record a redaction failure marker/count, not return the original unredacted preview.
- The library should not call redactors for pickle/binary rows that have no preview under the bounded preview policy.

Pre-implementation tests should cover:

- redactor receives bounded preview text and metadata
- redactor replacement text is returned
- redactor `None` suppresses preview
- redactor exceptions suppress previews without exposing original content
- redactor cannot access serialized keys through context
- truncation metadata survives redactor replacement/suppression
- redactor is not called for rows without previews

This design deliberately keeps redaction separate from serializer logic. Serializers define how values become bytes; inspection preview policy defines whether bytes are safely summarized; redactors define application-specific disclosure rules. Mixing those together creates a feature smoothie with security garnish.

Before implementing preview redaction, add tests for at least these cases:

- previews are omitted by default
- opt-in previews are marked sensitive in docs/API naming
- obvious JSON secret keys are redacted when a built-in policy is enabled
- caller-provided redactors can replace or suppress previews
- truncation state survives redaction
- redaction failures do not expose the original unredacted payload by accident

Before implementing `inspect_entries()`, add tests for at least these policy cases:

- JSON payload shorter than the limit previews as UTF-8 text.
- JSON payload longer than the limit is byte-truncated and marked truncated.
- Invalid UTF-8 does not raise during preview generation.
- Pickle payloads are not deserialized and return no preview or a binary marker.
- Inspection does not change cache stats, expiry, or last-accessed state.
- A configured maximum prevents callers from requesting unbounded previews.

Non-goals for the first inspection API:

- cross-process live monitoring
- schema migration
- payload repair
- stable SQLite table/column contracts
- automatic deserialization of untrusted pickle payloads
- guaranteed external audit-log semantics

This should stay a design note until a real user or release requirement needs it. The current supported interfaces are still `get()`, `set_value()`, `set_exception()`, `clear()`, `info()`, decorator `cache_info()`, and the documented serializer contracts.

## JSON adapter recipe for datetimes and bytes

`JsonCacheSerializer` intentionally supports only ordinary JSON-compatible values. If cached payloads need common Python scalar adapters such as `datetime` or `bytes`, write a custom `CacheSerializer` with an explicit tagged representation instead of silently teaching the built-in serializer Python-specific tricks.

Recommended recipe:

- Use a custom `content_type`, such as `application/json+datetime-bytes-example`, so rows written by the adapter are not mixed with plain `JsonCacheSerializer` rows.
- Convert `datetime` values to tagged ISO 8601 strings, for example `{"__type__": "datetime", "value": "2026-05-11T12:30:00+00:00"}`.
- Convert `bytes` values to tagged base64 strings, for example `{"__type__": "bytes", "value": "YWJjMTIz"}`.
- Recursively adapt lists and dictionaries. Keep dictionary keys as strings if other languages need to read the cache rows.
- Reject unsupported objects with `CacheSerializationError` rather than falling back to `repr()` or other lossy magic.
- Treat the tag names as part of the payload compatibility contract; change the namespace or content type if the adapter format changes.

Executable example: `docs/examples/disk_cache_backend_examples.py::json_datetime_bytes_serializer_example` defines `DateTimeBytesJsonSerializer`, stores a payload containing a timezone-aware `datetime` and `bytes`, and verifies the restored values match the originals.

This stays as a recipe rather than a built-in serializer for now. Date/time policy is application-specific: timezone handling, naive datetimes, binary encoding choices, and schema compatibility are all places where generic convenience grows little teeth.

## Non-goals for first implementation

- Cross-process locking guarantees beyond SQLite’s normal locking.
- Distributed cache behavior.
- Automatic schema migrations beyond initial table creation.
- Compression.
- Encryption.
- Async support.

## Implementation order

1. Add `DiskCacheBackend` skeleton and schema initialization.
2. Add key/payload serialization helpers.
3. Implement `get`, `set_value`, `set_exception`, `clear`, and `info`.
4. Add reusable backend conformance tests and run them against `MemoryCacheBackend` and `DiskCacheBackend`.
5. Add disk-specific tests for persistence across backend instances.
6. Add docs and README example.

## Implemented serialization helpers

`DiskCacheBackend` now has internal helpers for key and payload serialization:

- `_serialize_key(key)` uses `PickleCacheSerializer` for generated Python cache keys.
- `_serialize_payload(value)` uses the configured payload serializer.
- `_deserialize_payload(data)` uses the configured payload serializer.
- `serializer_content_type` exposes the configured payload serializer content type for row metadata.

The implementation stores serializer content type with each row. If a later backend instance uses a different serializer content type for the same database, matching rows are treated as misses and removed instead of being deserialized with the wrong serializer.

## Implemented cache operations

`DiskCacheBackend` now implements the `CacheBackend` protocol:

- `get()` returns valid entries, records hits/misses, deletes expired rows, updates `last_accessed` on hits, and refreshes `expires_at` on hits only when `refresh_ttl_on_hit=True`.
- `set_value()` stores successful values.
- `set_exception()` stores cached exceptions for `cache_exceptions=True` use.
- `clear()` deletes entries and resets hit/miss statistics.
- `info()` prunes expired rows and reports `CacheInfo`.

Operations after `close()` raise `CacheBackendClosedError`.

## Corrupt row handling

If a row has a matching serializer content type but the payload cannot be deserialized, `DiskCacheBackend.get()` treats it as a cache miss, deletes the bad row, records a miss, and returns `None`. Cache corruption should not break callers by default; the wrapped function can recompute the value and replace the row.

This policy is intentionally conservative for cache data: caches are disposable, but user calls should not fail just because the shoebox contains haunted bytes.

## SQLite operational tuning

`DiskCacheBackend` configures SQLite for local cache ergonomics:

- `PRAGMA busy_timeout = 5000` by default, also mirrored through the SQLite connection timeout.
- `PRAGMA journal_mode = WAL` by default for better local read/write behavior.
- `wal=False` is available for environments where WAL sidecar files are undesirable.

This remains a single-host local cache. SQLite handles its normal file locking, but this backend is not a distributed cache and does not promise cross-host filesystem semantics.

## Scoped context-manager use

`DiskCacheBackend` can be used as a context manager for short scoped backend operations:

```python
from useful_decorators import DiskCacheBackend

with DiskCacheBackend(".cache/tool.sqlite3", ttl=60, maxsize=16) as backend:
    backend.set_value("answer", "cached")
    entry = backend.get("answer")
```

Do not wrap a decorator-bound backend in a short `with` block unless all decorated calls happen before the block exits. Once the context manager closes the backend, later decorated calls will fail with `CacheBackendClosedError`.


## Persistence across backend instances

`DiskCacheBackend` stores cache entries in SQLite, so a later backend instance using the same database path can reuse entries written by an earlier backend instance. This is useful for CLIs, local tools, and service restarts where cache data is disposable but still worth keeping between runs.

For persistent cache reuse, treat cache keys as part of the on-disk compatibility contract:

- Use a stable `namespace` for each logical cache. Changing the namespace intentionally creates a separate cache key space.
- Keep call arguments and keyword names stable for values you expect to reuse. The default key is derived from the function call inputs plus `namespace`; different inputs are different cache entries.
- Keep `typed=True` consistent. Switching it changes whether argument types participate in generated keys.
- If you provide a custom `key` function, keep its output stable across releases and process restarts. A changed custom key function can orphan old cache rows.
- Changing serializers, payload types, or cache value schemas may make old rows disposable. Use `clear()` or a new namespace when old persistent values should not be reused.

## Integrity check and maintenance helper design

A future disk-cache maintenance helper should be explicit and operator-facing, not part of normal `get()` hot-path behavior. The intended public shape is a small method on `DiskCacheBackend`, tentatively `maintain()`, with a report object such as `DiskCacheMaintenanceReport`.

Planned call shape:

```python
report = backend.maintain(
    prune_expired=True,
    validate_payloads=False,
    vacuum=False,
)
```

The helper should support these maintenance actions deliberately:

- `prune_expired=True`: delete expired rows without waiting for individual lookups or `info()`.
- `validate_payloads=True`: scan rows whose `serializer_content_type` matches the active backend serializer and attempt payload deserialization, dropping rows that fail.
- serializer mismatch cleanup: count and optionally drop rows whose stored `serializer_content_type` does not match the active serializer.
- `vacuum=True`: run SQLite `VACUUM` only as an explicit operator choice, because it can be more expensive and may require exclusive database access.

The report should be structured rather than log-text-only. At minimum it should include:

- `rows_seen`
- `expired_rows_dropped`
- `serializer_mismatch_rows_dropped`
- `corrupt_payload_rows_dropped`
- `vacuum_ran`

Maintenance should reuse `DiskCacheDropEvent` / `on_drop` for rows it discards, using the same reasons as lookup-time cleanup where possible. That keeps diagnostics consistent instead of inventing a second tiny telemetry kingdom.

Non-goals for the first maintenance helper:

- repairing corrupted payloads
- migrating payload schemas automatically
- promising cross-host/shared-filesystem safety
- running `VACUUM` automatically from `get()`, `set_value()`, or `info()`
- raising on corrupt rows by default

The default posture remains cache-friendly: disposable rows can be pruned, counted, and logged, but normal callers should not fail just because the cache contains stale or malformed data.

## Cache versioning and schema changes

Before public release, treat persistent disk-cache reuse as a compatibility surface. If a cached value's meaning, payload shape, serializer, or trust boundary changes, do not silently reuse rows written by older code. Pick one of these strategies deliberately:

- Prefer a versioned namespace for long-lived persistent caches, such as `users:v1` or `ai-responses:v2`. Bump the namespace when cached value semantics or schemas change incompatibly.
- Use `cache_clear()` or backend `clear()` during upgrades when the entire cache should be discarded in place.
- Document any intentional reuse across versions when old rows are still valid.
- Avoid making custom `key` functions depend on unstable implementation details unless you also version the namespace.

The first implementation does not provide automatic schema migrations for cached payloads. Namespace versioning is the boring, explicit escape hatch. Boring is good here; haunted cache archaeology is not a feature.

## Disk-cache schema metadata table design

If a future release promises disk-cache file compatibility across package versions, add a small metadata table before making that promise. The metadata table should make compatibility checks explicit instead of inferring meaning from table shape, column presence, or vibes.

Tentative schema:

```sql
CREATE TABLE IF NOT EXISTS cache_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Initial rows could include:

- `schema_version`: integer string for the SQLite schema contract, starting at `1`.
- `created_by`: package name, such as `useful-decorators`.
- `created_with_version`: package version that initialized the file, for diagnostics only.
- `updated_with_version`: last package version that opened or migrated the file, for diagnostics only.

Design constraints:

- Schema metadata is about the disk-cache container format, not cached payload schemas. Payload compatibility still belongs to namespaces, serializers, and application-owned value semantics.
- Unknown future major schema versions should fail closed with a clear `ConfigurationError` or disk-cache-specific exception rather than silently reading rows with the wrong assumptions.
- Older known schema versions may be migrated only by explicit, tested migration code. No best-effort table poking in constructors.
- Metadata writes should happen in the same initialization/migration transaction as schema changes. Half-upgraded cache files are how gremlins get promoted.
- Diagnostics may expose metadata through a future inspection API, but callers should not need to query `cache_metadata` directly.

Non-goals for the first metadata table:

- payload schema migration
- serializer migration
- cross-host locking semantics
- user data durability guarantees
- semver promises for every SQLite implementation detail

Until file compatibility is a public promise, this remains a design note. Current caches are disposable local caches; clearing or versioning namespaces is still the preferred answer for incompatible changes.

Close each backend instance when its owner is done with it. See `docs/examples/disk_cache_backend_examples.py` for the executable persistence example used by the documentation test suite.
