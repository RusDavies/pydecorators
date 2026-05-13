# Release note template

Use this template when drafting a release that changes cache behavior, serialized payloads, decorator defaults, or public exceptions.

## Compatibility

- Python support: no change / changed to ...
- Public API: no change / changed ...
- Persistent cache compatibility: no change / incompatible / migration recommended
- Disk cache schema: unchanged / changed from ... to ...
- Recommended operator action: none / clear cache namespace / bump namespace version / run migration

## Persistent cache compatibility note

If a release changes cache key construction, serializer expectations, disk schema behavior, or default namespace guidance, include a short note like this:

> Persistent disk caches created by earlier versions remain compatible. If you change your serializer or key namespace, prefer a new namespace such as `my-app:v2` rather than reusing incompatible rows.

For incompatible changes, say so plainly and include the safest cleanup path. Cache surprises are only funny when they happen to somebody else's demo.
