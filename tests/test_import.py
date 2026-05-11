import useful_decorators


def test_package_exports_version() -> None:
    assert useful_decorators.__version__ == "0.1.0"
