# Django and FastAPI Usage Examples

These examples show where to put decorators in framework applications without making `pydecorators` depend on Django, FastAPI, Starlette, or ASGI internals.

## Keep decorators on helpers, not framework wrappers

Prefer decorating service helpers, dependency functions, repository calls, or expensive computations. Leave the framework route/view wrapper boring unless the decorator is explicitly designed for request/response objects.

Good targets:

- a Django view helper that loads a profile
- a FastAPI dependency/helper that loads tenant settings
- an outbound service-client function wrapped with `@retry`
- a cache backend created during application startup and closed during shutdown

Riskier targets:

- decorating request objects directly without a custom cache key
- caching full response objects that contain user/session-specific headers
- retrying non-idempotent POST/payment/write operations by default
- creating a decorator-bound `DiskCacheBackend` inside a per-request scope

## Cache lifecycle

For web services, create long-lived cache backends during application startup and close them from shutdown hooks. The executable examples use tiny stand-ins instead of importing Django/FastAPI so the docs stay dependency-free while still testing the recommended shape.

Use `cache_directory("app-name")` or a framework-configured cache/state directory to keep SQLite files out of public/static/media roots. Cache files and inspection reports can contain sensitive operational metadata.

## Executable examples

See `docs/examples/web_framework_examples.py` for tested examples covering:

- Django-style cached view helpers
- FastAPI-style cached dependency helpers
- service cache path selection
- retrying service-client helpers outside route wrappers

The examples intentionally avoid framework imports. Framework-specific code usually needs local application settings, lifecycle hooks, and auth boundaries; fake imports in docs are how folklore gains tenure.
