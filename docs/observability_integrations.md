# Optional Observability Integrations

`blakemere-decorators` stays dependency-light. OpenTelemetry, Prometheus, and structlog integrations are supported through ordinary callback/logger adapter patterns rather than hard runtime dependencies.

## OpenTelemetry

Use `measure_time(callback=...)` to translate `TimingInfo` into span attributes or events. Keep tracer/provider setup in the application, then pass a tiny callback into the decorator. The package should not configure global telemetry providers on import.

## Prometheus

Use `measure_time(callback=...)`, retry hooks, or cache-info polling to update application-owned counters/histograms. Keep metric names, labels, registries, and scrape/export policy in the application. Avoid high-cardinality labels such as raw arguments, user IDs, tenant names, URLs with IDs, or exception messages.

## structlog

`log_calls` accepts a standard `logging.Logger`-style object. For structlog, use a small adapter that exposes `.log(level, message, *args, **kwargs)` and forwards structured fields to an application-owned structlog logger. Keep redaction settings explicit with `redact_args` and `summarize_result`.

## Executable examples

See `docs/examples/observability_integration_examples.py` for dependency-free examples covering:

- OpenTelemetry-style timing spans
- Prometheus-style duration histograms
- structlog-style `log_calls` adaptation
- structured retry attempt events

The examples intentionally use fake tracer/histogram/logger objects. Real applications own exporter setup, registries, sampling, retention, and whatever delightful YAML swamp their platform requires.
