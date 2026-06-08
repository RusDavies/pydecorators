import pydecorators


def test_package_exports_version() -> None:
    assert pydecorators.__version__ == "0.2.0"
