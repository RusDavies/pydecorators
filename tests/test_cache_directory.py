"""Tests for cache directory path helper."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pydecorators import ConfigurationError, cache_directory


def test_cache_directory_uses_explicit_base_path() -> None:
    assert cache_directory("tool-cache", base_path="~/tmp") == (
        Path("~/tmp").expanduser() / "tool-cache"
    )


def test_cache_directory_rejects_empty_app_name() -> None:
    with pytest.raises(ConfigurationError, match="app name must not be empty"):
        cache_directory("  ")


def test_cache_directory_rejects_nested_app_name() -> None:
    with pytest.raises(ConfigurationError, match="single path segment"):
        cache_directory("tool/cache")


def test_cache_directory_uses_xdg_cache_home_on_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/cache-root")

    assert cache_directory("demo") == Path("/tmp/cache-root/demo")


def test_cache_directory_uses_platform_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    monkeypatch.setattr(sys, "platform", "darwin")
    assert cache_directory("demo") == Path.home() / "Library" / "Caches" / "demo"

    monkeypatch.setattr(sys, "platform", "win32")
    assert cache_directory("demo") == Path.home() / "AppData" / "Local" / "demo"
