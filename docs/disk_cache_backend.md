# `DiskCacheBackend` Design

`DiskCacheBackend` should provide persistent local cache storage for `@cache_result` using SQLite from the Python standard library.

The goal is a durable cache for CLIs, scripts, local tools, and single-host services. It is not a distributed cache and should not pretend to be one while wearing a fake moustache.

## Recommended public shape

```python
from pathlib import Path
from useful_decorators import DiskCacheBackend, PickleCacheSerializer

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
        serializer: CacheSerializer | None = None,
        clock: Clock | None = None,
        busy_timeout_ms: int = 5_000,
        wal: bool = True,
    ) -> None: ...
```

- `path`: SQLite database path.
- `ttl`: optional entry lifetime in seconds.
- `maxsize`: optional maximum entry count.
- `serializer`: payload serializer; defaults to `PickleCacheSerializer`.
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

Payloads use the configured `CacheSerializer`.

- Successful values store `is_exception=0`.
- Cached exceptions store `is_exception=1`.
- Store `serializer_content_type` with each row so future migrations or debugging can detect format mismatches.

## TTL behavior

- `expires_at` is computed at write time as `clock() + ttl`.
- `None` means no TTL expiry.
- Reads treat expired rows as misses and delete the expired row.
- `info()` prunes expired rows before reporting `currsize`.
- Cache hits do not refresh TTL in the first implementation.

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
- Prefer a custom JSON serializer for simple cross-language or lower-risk payloads once available.

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

- `get()` returns valid entries, records hits/misses, deletes expired rows, and updates `last_accessed` on hits.
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
