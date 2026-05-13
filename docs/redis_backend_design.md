# Redis Backend Design Notes

`RedisCacheBackend` is not implemented yet. This page records the key-space decisions that should be treated as the starting contract when the optional Redis backend is added.

## Key prefix policy

Redis keys should use a package-owned, versioned prefix:

```text
useful-decorators:{schema_version}:{namespace}:{key_digest}
```

Initial values:

- `schema_version`: `v1` for the first Redis storage format.
- `namespace`: the explicit `@cache_result(namespace=...)` value when present, otherwise a documented default such as `_default`.
- `key_digest`: SHA-256 hex digest of the serialized cache key, not the raw argument representation.

The prefix must make unrelated applications unlikely to collide while keeping raw cache keys out of Redis key listings. Raw keys can contain tenant names, user identifiers, or argument values. Redis key names get logged, monitored, sampled, and pasted into tickets with depressing regularity, so they should be boring digests rather than accidental data exports.

## Stats key naming

Stats should be stored separately from values with an explicit stats marker:

```text
useful-decorators:{schema_version}:{namespace}:stats
```

The stats value should be a Redis hash with at least:

- `hits`
- `misses`

If future metrics add counters, prefer additive hash fields over changing the key shape.

## Value key metadata

Each value key should store enough metadata to preserve existing cache semantics:

- serialized payload bytes
- serializer content type
- exception/value marker
- expiry policy compatible with `ttl`

Use native Redis expiry for TTL whenever possible so stale rows disappear without a separate sweeper. Do not use Redis expiry for hit/miss stats keys unless a future design deliberately makes stats disposable per deployment window.

## Compatibility and migration

Changing the Redis prefix, schema version, serializer format, or stats key naming is a cache-compatibility event. Prefer bumping `schema_version` and abandoning old keys over parsing unknown historical formats. Redis caches are disposable; surprise cross-version reads are the more interesting foot-gun.

## Optional dependency behavior

When the Redis backend is eventually implemented, importing the base package must not require Redis dependencies. Missing Redis extras should fail only when the Redis backend is imported or constructed, and the error message should point to the documented extra name.
