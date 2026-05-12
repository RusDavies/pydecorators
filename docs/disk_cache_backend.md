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

Close each backend instance when its owner is done with it. See `docs/examples/disk_cache_backend_examples.py` for the executable persistence example used by the documentation test suite.
