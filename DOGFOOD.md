# Dogfood Plan

Dogfood scenarios are kept as release gates so packaging, install behavior, and realistic decorator composition stay exercised outside the source checkout.

The current distribution name is `blakemere-wraptools`; the import package remains `pydecorators`.

## Goals

- Install the built wheel in a clean virtual environment.
- Run realistic scripts from outside the source checkout.
- Exercise decorator composition instead of only single-decorator happy paths.
- Record findings before each release when dogfood scripts expose sharp edges.

## Dogfood harness

Run:

```bash
python scripts/dogfood_local_wheel.py
python scripts/dogfood_external_project.py
```

The harness:

1. Builds a local wheel.
2. Creates a clean virtual environment.
3. Installs the wheel.
4. Runs dogfood scripts from `dogfood/` with `PYTHONPATH` cleared.

## Dogfood scenarios

- `dogfood/service_client.py`: combines `@require_env`, `@rate_limit`, `@retry`, `@timeout`, `@log_calls`, `@measure_time`, and `@circuit_breaker` in service-client-like sync and async flows.
- `scripts/dogfood_external_project.py`: optionally runs decorators from the installed wheel against a caller-provided external script without modifying that project. Set `PYDECORATORS_EXTERNAL_DOGFOOD_SCRIPT=/path/to/script.py` to enable this scenario; otherwise it skips cleanly.

## Findings log

Add findings here as dogfood scripts expose sharp edges.

- 2026-05-12: Initial harness added. No API changes required yet; first goal is keeping composition behavior executable from an installed wheel.
- 2026-05-12: External local-project dogfood against a sibling project script passed without API changes. Dynamic wrapping worked, but it reinforced that composition docs should eventually explain decorator order for wrappers that log/retry/measure.
- 2026-05-12: Resolved the wrapper-order documentation finding by adding `docs/composition.md` and linking it from the docs index and README. No API changes required.

## Release gate

Before each release:

- [x] Run `python scripts/dogfood_local_wheel.py` for `v0.1.0`.
- [x] Run `python scripts/dogfood_external_project.py` for `v0.1.0`.
- [x] Review this findings log for `v0.1.0`.
- [x] Resolve or explicitly defer any API/documentation issues found during dogfood use.
- [x] Publish `blakemere-wraptools` `0.1.0` to TestPyPI and PyPI.

- 2026-05-20: `blakemere-wraptools` `0.1.0` was published to TestPyPI and PyPI after the dogfood and release workflow gates passed.
