from pathlib import Path


def test_dogfood_plan_documents_release_pause_and_harness() -> None:
    text = Path("DOGFOOD.md").read_text()

    assert "Public publishing is intentionally paused" in text
    assert "blakemere-wraptools" in text
    assert "python scripts/dogfood_local_wheel.py" in text
    assert "python scripts/dogfood_external_project.py" in text
    assert "dogfood/service_client.py" in text
    assert "model-gateway-reliability-mini-lab" in text
    assert "Release gate" in text


def test_dogfood_harness_and_scenarios_exist() -> None:
    assert Path("scripts/dogfood_local_wheel.py").exists()
    assert Path("scripts/dogfood_external_project.py").exists()
    assert Path("dogfood/service_client.py").exists()


def test_dogfood_service_client_exercises_decorator_composition() -> None:
    text = Path("dogfood/service_client.py").read_text()

    for required in [
        "@measure_time",
        "@log_calls",
        "@require_env",
        "@rate_limit",
        "@retry",
        "@validate_types",
        "@timeout",
        "@circuit_breaker",
    ]:
        assert required in text
