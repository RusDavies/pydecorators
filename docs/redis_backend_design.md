# Redis Backend Design Notes

`RedisCacheBackend` is implemented as an optional cache backend. This page records the key-space decisions that should be treated as the compatibility contract for the Redis storage format.

Redis is not just a larger dictionary with a network cable attached. Moving cache state
out of the Python process changes the operating model: multiple workers can now share
entries, but every cache operation can also fail because of network, authentication,
server, deployment, or serialization problems. Treat it as shared infrastructure, not a
free upgrade from `dict`.

Use the Redis backend when shared cache state is worth the extra dependency and failure
surface. Keep the in-memory or disk backends when the cache only needs to serve one
process or one host. The dull option is often the correct one, which is rude but useful.

## Key prefix policy

Redis keys should use a package-owned, versioned prefix:

```text
blakemere-wraptools:{schema_version}:{namespace}:{key_digest}
```

Initial values:

- `schema_version`: `v1` for the first Redis storage format.
- `namespace`: the explicit `@cache_result(namespace=...)` value when present, otherwise a documented default such as `_default`.
- `key_digest`: SHA-256 hex digest of the serialized cache key, not the raw argument representation.

The prefix must make unrelated applications unlikely to collide while keeping raw cache keys out of Redis key listings. Raw keys can contain tenant names, user identifiers, or argument values. Redis key names get logged, monitored, sampled, and pasted into tickets with depressing regularity, so they should be boring digests rather than accidental data exports.

`RedisCacheBackend.key_prefix` is treated as a literal namespace prefix. It must not contain Redis glob metacharacters (`*`, `?`, `[`, or `]`) because backend maintenance operations use Redis `SCAN MATCH` patterns for clear, info, and eviction paths. If an application needs user- or tenant-derived namespace text, validate it against a small allowlist or hash/encode it before passing it as `key_prefix`. Shared-cache namespaces are not where we practice interpretive dance.

## Stats key naming

Stats should be stored separately from values with an explicit stats marker:

```text
blakemere-wraptools:{schema_version}:{namespace}:stats
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

## Operating model

Redis changes five things that callers and maintainers should understand.

### Shared state

All processes using the same Redis deployment, schema version, and namespace share cache
entries. That is the point, but it means namespace choice becomes an isolation boundary.
Use distinct namespaces for applications, tenants, environments, or incompatible value
semantics. A staging worker reading production-shaped keys is not clever reuse; it is a
bug wearing a cost-saving hat.

### Network and server failure

A Redis lookup can fail before the wrapped function runs. A write can fail after the
wrapped function succeeds. Those are different failure modes, and neither should be
hidden under vague "cache unavailable" language.

The backend should be explicit about whether a Redis failure is surfaced to the caller or
treated as a cache miss/write-drop. Silent degradation is attractive until it erases the
only signal that the cache tier is on fire.

### Expiry semantics

Redis TTL is server-side wall-clock behavior, not the injected monotonic test clock used
by in-process backends. That is the right trade-off for shared expiry, but it means tests
and diagnostics should not pretend Redis expiry works exactly like local clock-driven
eviction.

Refreshing TTL on hit must update the Redis expiry atomically with the read/update path
where practical. Otherwise hot keys can expire while callers believe they are keeping the
entry alive.

### Deployment burden

The Redis backend adds an operational dependency: connection URLs, authentication, TLS,
timeouts, pool sizing, deployment topology, backups or deliberate non-backups, and key
cleanup. The library should keep the API small, but documentation should not imply Redis
is free because installation fits in one optional extra.

### Observability

Shared caches need inspection. At minimum, applications should be able to observe hit and
miss counts, connection failures, serialization failures, dropped writes, and suspicious
namespace growth. Without that, Redis becomes a dark cupboard where latency goes to make
poor life choices.

Stats keys are deliberately separate from value keys so operators can inspect cache
behavior without sampling payload keys or exposing raw argument data.

## Compatibility and migration

Changing the Redis prefix, schema version, serializer format, or stats key naming is a cache-compatibility event. Prefer bumping `schema_version` and abandoning old keys over parsing unknown historical formats. Redis caches are disposable; surprise cross-version reads are the more interesting foot-gun.

## Optional dependency behavior

The base package must not require Redis dependencies. Importing `pydecorators.redis_backend` also stays dependency-light. Missing Redis extras fail only when the Redis backend is imported or constructed with `RedisCacheBackend(url=...)`; applications that already own Redis client construction can pass `client=...` without importing `redis-py` through this package.

Tests assert that the base package imports without Redis installed, the backend module imports without Redis installed, and URL construction points users at `blakemere-wraptools[redis]` when the optional dependency is missing.
