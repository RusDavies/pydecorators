# Security Hardening Guide

PyDecorators is a small in-process helper library, not a security product. That distinction matters. The decorators can make unsafe code easier to observe, retry, cache, or validate; they cannot turn unsafe trust boundaries into safe ones by sheer optimism, which remains a poor engineering strategy.

Use this page as the central checklist for cache, logging, validation, and operational hardening before using the package in applications that handle secrets, customer data, or production traffic.

## Threat model summary

Assume attackers may influence function arguments, return values, exception text, environment configuration, cache keys, cache values, logs, and deployment paths. Do not assume decorators create a new isolation boundary. They run inside the same Python process as the wrapped function.

The safest default posture is:

- cache only disposable values;
- serialize only data you trust;
- log less than you think you need;
- validate inputs at real system boundaries;
- treat in-process controls as local safeguards, not distributed enforcement.

## Disk cache trust boundaries

`DiskCacheBackend` uses SQLite for persistence. The default payload serializer uses pickle, so cache databases are trusted local files only.

Hardening rules:

- Do not load cache databases supplied by users, downloads, support tickets, or other untrusted sources.
- Do not place cache files in world-writable directories.
- Prefer per-application cache directories with restrictive permissions.
- Treat cache contents as sensitive if cached values, keys, or exception payloads may contain secrets or personal data.
- Clear or rotate cache files when serializer behavior, value semantics, or namespace meaning changes.
- Use `JsonCacheSerializer` for simple JSON-compatible values when cross-language inspection or pickle avoidance matters.

See [`DiskCacheBackend`](https://github.com/RusDavies/pydecorators/blob/master/docs/disk_cache_backend.md) and [`@cache_result`](https://github.com/RusDavies/pydecorators/blob/master/docs/cache_result.md) for backend lifecycle and serializer details.

## Cache key and value hygiene

Cache keys and values often preserve more context than intended. A key function that includes a token, email address, tenant identifier, or request object can quietly create a data-retention problem.

Prefer:

- stable non-secret identifiers over raw tokens or credentials;
- explicit namespaces for shared backends;
- bounded cache sizes and TTLs;
- cache values that can be regenerated safely;
- custom serializers only when their compatibility and failure behavior are understood.

Avoid caching:

- authentication secrets;
- authorization decisions without careful invalidation;
- raw request/response payloads containing personal data;
- exceptions that include credentials or sensitive upstream details.

## Logging safety

`@log_calls` can log arguments, return values, exceptions, and duration. That is useful. It is also how secrets achieve immortality.

Hardening rules:

- Keep argument logging disabled unless needed.
- Use `redact_args` for known sensitive parameter names such as `password`, `token`, `api_key`, and `authorization`.
- Avoid result logging for functions that return secrets, customer records, access tokens, or large payloads.
- Route logs to systems with appropriate access controls and retention policies.
- Remember that exception messages may contain sensitive upstream data.

See [`@log_calls`](https://github.com/RusDavies/pydecorators/blob/master/docs/log_calls.md) for redaction options and logging behavior.

## Runtime validation limits

`@validate_types` is a lightweight developer aid. It is not schema validation, input sanitization, authorization, or a deserialization firewall.

Use it to catch obvious mistakes near internal function boundaries. For public APIs, message queues, webhooks, CLI inputs, files, or user-submitted data, use purpose-built validation and parsing at the boundary before values reach business logic.

See [`@validate_types`](https://github.com/RusDavies/pydecorators/blob/master/docs/validate_types.md) for supported annotations and limitations.

## In-process control limits

`@rate_limit` and `@circuit_breaker` protect one Python process. They do not coordinate across multiple workers, containers, hosts, or serverless instances.

For distributed systems:

- enforce rate limits at a shared gateway, proxy, API-management layer, or distributed store;
- use service-level circuit breaking, timeouts, and backpressure where available;
- treat decorator-level controls as local defense-in-depth;
- test multi-worker behavior explicitly instead of assuming one process tells the whole herd what to do. The herd, naturally, has not read your decorator.

See [`@rate_limit`](https://github.com/RusDavies/pydecorators/blob/master/docs/rate_limit.md), [`@circuit_breaker`](https://github.com/RusDavies/pydecorators/blob/master/docs/circuit_breaker.md), and [`Decorator composition`](https://github.com/RusDavies/pydecorators/blob/master/docs/composition.md) for local behavior and stacking guidance.

## Environment variables and secrets

`@require_env` checks whether required environment variables exist and optionally pass validators. It does not store, rotate, encrypt, or protect secrets.

Hardening rules:

- Use a real secret-management system for production secrets.
- Do not log environment values.
- Prefer validators that check shape or presence, not secret contents.
- Fail closed when required configuration is absent.

See [`@require_env`](https://github.com/RusDavies/pydecorators/blob/master/docs/require_env.md) for validator behavior.

## Safe defaults checklist

Before production use, confirm:

- [ ] Disk cache files live in restricted, application-owned paths.
- [ ] Pickle-backed caches are never loaded from untrusted sources.
- [ ] Cache keys do not include raw secrets.
- [ ] Cache TTLs and sizes are bounded where retention matters.
- [ ] Logging of arguments and results is deliberately enabled, not accidental.
- [ ] Sensitive log arguments are redacted.
- [ ] Runtime type validation is not treated as external input validation.
- [ ] Rate limits and circuit breakers are backed by distributed controls when deployed across multiple workers.
- [ ] Environment-variable checks are paired with proper secret management.

## Release review notes

When adding a new decorator or backend, update this page if the feature can persist data, emit data, validate data, deserialize data, call external systems repeatedly, or change failure behavior. If that sentence sounds broad, good. Security footnotes age poorly when they are hidden in six different files like cursed confetti.
