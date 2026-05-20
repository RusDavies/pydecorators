import json
from email.message import Message
from urllib.error import HTTPError, URLError

import pytest
from scripts import check_package_name_availability as checker


def test_check_repository_reports_404_as_available(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(url: str, timeout: float) -> object:
        raise HTTPError(url, 404, "Not Found", hdrs=Message(), fp=None)

    monkeypatch.setattr(checker, "urlopen", fake_urlopen)

    status = checker.check_repository("pypi", "pydecorators", timeout=1.0)

    assert not status.exists
    assert status.detail == "404 Not Found"
    assert status.repository == "pypi"


def test_check_repository_reports_existing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"info": {"version": "1.2.3"}}).encode()

    def fake_urlopen(url: str, timeout: float) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(checker, "urlopen", fake_urlopen)

    status = checker.check_repository("testpypi", "pydecorators", timeout=1.0)

    assert status.exists
    assert status.detail == "published version 1.2.3"
    assert status.repository == "testpypi"


def test_check_repository_fails_loudly_on_network_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(url: str, timeout: float) -> object:
        raise URLError("offline")

    monkeypatch.setattr(checker, "urlopen", fake_urlopen)

    with pytest.raises(SystemExit, match="failed to check"):
        checker.check_repository("pypi", "pydecorators", timeout=1.0)


def test_main_returns_nonzero_when_name_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    statuses = [
        checker.PackageStatus("pypi", "https://example.test", exists=False, detail="404"),
        checker.PackageStatus("testpypi", "https://example.test", exists=True, detail="1.0"),
    ]

    monkeypatch.setattr(checker, "check_repository", lambda *args: statuses.pop(0))

    assert checker.main(["--name", "example-package"]) == 1
