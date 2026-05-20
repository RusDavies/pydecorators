# Dogfood Plan

Public publishing is intentionally paused until the package has been used locally enough to expose awkward APIs, decorator-composition problems, documentation gaps, and release-process surprises.

The current distribution name is `blakemere-wraptools`; the import package remains `pydecorators`.

## Goals

- Install the built wheel in a clean virtual environment.
- Run realistic scripts from outside the source checkout.
- Exercise decorator composition instead of only single-decorator happy paths.
- Record findings before TestPyPI/PyPI release.

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
- `scripts/dogfood_external_project.py`: runs decorators from the installed wheel against `projects/model-gateway-reliability-mini-lab/gateway_sim.py` without modifying that project.

## Findings log

Add findings here as dogfood scripts expose sharp edges.

- 2026-05-12: Initial harness added. No API changes required yet; first goal is keeping composition behavior executable from an installed wheel.
- 2026-05-12: External local-project dogfood against `model-gateway-reliability-mini-lab/gateway_sim.py` passed without API changes. Dynamic wrapping worked, but it reinforced that composition docs should eventually explain decorator order for wrappers that log/retry/measure.
- 2026-05-12: Resolved the wrapper-order documentation finding by adding `docs/composition.md` and linking it from the docs index and README. No API changes required.

## Release gate

Before publishing:

- [ ] Run `python scripts/dogfood_local_wheel.py`.
- [ ] Run `python scripts/dogfood_external_project.py`.
- [ ] Review this findings log.
- [x] Resolve or explicitly defer any API/documentation issues found during dogfood use.
- [ ] Re-check `pydecorators` availability on PyPI/TestPyPI.
