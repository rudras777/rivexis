# Observability and OpenTelemetry — P35

Rivexis retains W3C Trace Context correlation and optional OTLP/HTTP protobuf export through the official OpenTelemetry Python SDK/exporter. Telemetry is disabled by default and does not open a network exporter unless `RIVEXIS_OTEL_ENABLED=true` and an endpoint is configured.

## P35 confidentiality contract

Telemetry is an external disclosure boundary. Provider/RPC endpoints may contain secrets and concrete HTTP paths may contain tenant/resource identifiers. P35 therefore:

- exports sanitized provider provenance rather than raw provider/RPC URLs;
- names HTTP server spans from FastAPI route templates and emits `http.route` rather than concrete resource paths;
- omits alert IDs from delivery spans;
- records exception type/class and ERROR status only—never raw exception messages or stack traces through the Rivexis tracing helpers;
- requires HTTPS for non-loopback OTLP collectors in production;
- permits HTTP only for loopback collectors (`localhost`, `127.0.0.1`, `::1`);
- rejects OTLP endpoint userinfo, query strings and fragments.

Configuration follows the OpenTelemetry OTLP contract. Set `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` for the exact traces endpoint, or `OTEL_EXPORTER_OTLP_ENDPOINT` as a base endpoint (Rivexis resolves `/v1/traces`). `OTEL_SERVICE_NAME` defaults to `rivexis-api`.

`scripts/certify_otlp_export.py` starts a loopback collector stub, emits linked server/child spans plus a sentinel exception, parses the OTLP protobuf and verifies trace ID preservation, parent linkage, content type, `/v1/traces` delivery, exception-class presence and absence of the sentinel exception message/stacktrace payload. This certifies Rivexis' local export implementation; it does not certify a production collector's own retention, access-control or sampling policy.

Authenticated `GET /api/v1/observability/status` exposes exporter health state without exposing collector credentials. Production provider diagnostic routes do not allow tenant-triggered deep probes; trusted release certification performs provider probes directly from the controlled runner.
