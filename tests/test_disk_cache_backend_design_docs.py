from pathlib import Path


def test_disk_cache_backend_design_doc_covers_required_decisions() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "SQLite",
        "cache_entries",
        "cache_stats",
        "PickleCacheSerializer",
        "CacheSerializer",
        "expires_at",
        "last_accessed",
        "CacheInfo",
        "RLock",
        "check_same_thread=False",
        "Trust boundary warning",
        "pickle",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_persistent_key_stability() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "For persistent cache reuse",
        "on-disk compatibility contract",
        "stable `namespace`",
        "Changing the namespace intentionally creates a separate cache key space",
        "call arguments and keyword names stable",
        "`typed=True` consistent",
        "custom `key` function",
        "orphan old cache rows",
        "Use `clear()` or a new namespace",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_cache_versioning_guidance() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Cache versioning and schema changes",
        "persistent disk-cache reuse as a compatibility surface",
        "versioned namespace",
        "users:v1",
        "Bump the namespace",
        "cache_clear()",
        "backend `clear()`",
        "automatic schema migrations",
        "Namespace versioning",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_maintenance_helper_design() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Integrity check and maintenance helper design",
        "maintain()",
        "DiskCacheMaintenanceReport",
        "prune_expired=True",
        "validate_payloads=True",
        "serializer mismatch cleanup",
        "vacuum=True",
        "rows_seen",
        "expired_rows_dropped",
        "serializer_mismatch_rows_dropped",
        "corrupt_payload_rows_dropped",
        "DiskCacheDropEvent",
        "Non-goals for the first maintenance helper",
        "repairing corrupted payloads",
        "migrating payload schemas automatically",
        "running `VACUUM` automatically",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_sqlite_column_stability() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## SQLite column stability for debugging",
        "Direct SQLite inspection is supported only as a debugging aid",
        "Debugging-friendly columns",
        "`payload`",
        "`serializer_content_type`",
        "`is_exception`",
        "`created_at`, `last_accessed`, and `expires_at`",
        "Internal implementation details",
        "`key`: an internal serialized cache key",
        "The shape of `cache_stats` is internal",
        "backend.info()",
        "cache_info()",
        "add an explicit API instead of scraping",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_inspection_api_design() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Supported cache-inspection API design",
        "DiskCacheInspectionEntry",
        "DiskCacheInspectionReport",
        "inspect_entries",
        "read-only",
        "should not expose serialized `key` bytes by default",
        "key_sha256",
        "Payload previews should be best-effort and bounded",
        "report serializer content type and payload byte size",
        "explicit `limit`/pagination behavior",
        "structured data suitable for a future CLI",
        "Non-goals for the first inspection API",
        "automatic deserialization of untrusted pickle payloads",
        "stay a design note until a real user or release requirement needs it",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_schema_metadata_design() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Disk-cache schema metadata table design",
        "cache_metadata",
        "schema_version",
        "created_by",
        "created_with_version",
        "updated_with_version",
        "disk-cache container format",
        "Payload compatibility still belongs to namespaces",
        "Unknown future major schema versions should fail closed",
        "explicit, tested migration code",
        "same initialization/migration transaction",
        "Non-goals for the first metadata table",
        "payload schema migration",
        "serializer migration",
        "remains a design note",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_bounded_preview_policy() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Bounded payload preview policy design",
        "include_payload_preview=False",
        "payload_preview_max_bytes=256",
        "4096",
        "payload_preview_truncated",
        'errors="replace"',
        "Invalid UTF-8 should never fail inspection",
        "Binary, pickle, and unknown serializers should not be deserialized",
        "Pickle previews must never call `pickle.loads()`",
        "should not update `last_accessed`, hits, misses, TTL, or LRU state",
        "JSON payload longer than the limit is byte-truncated",
        "Inspection does not change cache stats",
        "prevents callers from requesting unbounded previews",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_preview_redaction_expectations() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## Payload preview redaction expectations",
        "cached return values may contain secrets",
        "Previews should be opt-in",
        "should not promise automatic secret detection",
        "preview_redactor",
        "password",
        "authorization",
        "Redaction should happen after bounded decoding/truncation",
        "Inspection output should not be logged automatically",
        "support bundles",
        "pastebins",
        "redaction failures do not expose the original unredacted payload",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_preview_redactor_callback_design() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## `preview_redactor` callback design",
        "DiskCachePreviewContext",
        "PreviewRedactor",
        "already bounded/decoded preview string",
        "Returning `None` suppresses the preview",
        "should not receive serialized keys",
        "run after truncation and basic decoding",
        "redaction failure marker/count",
        "not return the original unredacted preview",
        "redactor replacement text is returned",
        "redactor exceptions suppress previews",
        "redactor is not called for rows without previews",
        "keeps redaction separate from serializer logic",
    ]:
        assert required in text


def test_disk_cache_backend_design_doc_covers_no_preview_safe_mode() -> None:
    text = Path("docs/disk_cache_backend.md").read_text()

    for required in [
        "## No-preview support bundle and CI mode",
        "support bundles",
        "CI artifacts",
        "include_payload_preview=False",
        "must not include payload preview text",
        "raw payload bytes",
        "serialized cache keys",
        "deserialized values",
        "should not invoke `preview_redactor`",
        "lower-risk, not risk-free",
        "--include-payload-preview",
        "safe mode never calls caller-provided redactors",
    ]:
        assert required in text
