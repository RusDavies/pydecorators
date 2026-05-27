from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_policy


def test_redis_pickle_trust_boundary_is_documented_in_user_facing_docs() -> None:
    docs = {
        "README.md": Path("README.md").read_text(),
        "docs/API_REFERENCE.md": Path("docs/API_REFERENCE.md").read_text(),
        "docs/PUBLIC_API.md": Path("docs/PUBLIC_API.md").read_text(),
        "docs/redis_backend_design.md": Path("docs/redis_backend_design.md").read_text(),
        "docs/security_hardening.md": Path("docs/security_hardening.md").read_text(),
    }

    for path, text in docs.items():
        assert "RedisCacheBackend" in text, path
        assert "PickleCacheSerializer" in text, path
        assert "JsonCacheSerializer" in text, path
        assert "trusted" in text.lower(), path
        assert "untrusted" in text.lower(), path
