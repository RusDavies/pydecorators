# Redis Backend Design Notes

`RedisCacheBackend` is implemented as an optional cache backend. This page records the key-space decisions that should be treated as the compatibility contract for the Redis storage format.

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

The base package must not require Redis dependencies. Importing `useful_decorators.redis_backend` also stays dependency-light. Missing Redis extras fail only when the Redis backend is imported or constructed with `RedisCacheBackend(url=...)`; applications that already own Redis client construction can pass `client=...` without importing `redis-py` through this package.

Tests assert that the base package imports without Redis installed, the backend module imports without Redis installed, and URL construction points users at `blakemere-decorators[redis]` when the optional dependency is missing.
