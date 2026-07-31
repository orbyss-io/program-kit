# Deterministic .NET diagnostics and telemetry composition

Program Kit generates provider-neutral emission through typed `ILogger<T>`,
`ActivitySource`, and `Meter`. A generated host optionally selects the exact
OpenTelemetry .NET adapter; OpenTelemetry does not own operation meaning.

The initial profile pins OpenTelemetry .NET 1.17.0 and separately records the
OpenTelemetry specification and semantic-convention revisions. Only the stable
HTTP conventions emitted by the pinned ASP.NET Core and HttpClient
instrumentation are accepted. No mixed or developmental convention group is
enabled through an ambient stability opt-in.

Logger category marker types, event IDs, event names, templates, bounded
correlation scopes, activity sources,
activity names and kinds, meter names, instruments, units, and attribute
catalogs are explicit. Metric and activity attributes must be non-sensitive
and select a value from a finite reviewed catalog within their cardinality
bound. Generated custom activities cannot use
`Server` or `Client`, because those spans belong to the selected framework
instrumentation.

W3C Trace Context is the base propagation profile. The initial adapter forwards
no baggage. A non-empty baggage allowlist requires a future exact adapter that
proves extraction, injection, validation, and non-authoritative handling; it
cannot establish identity or authorization.

HTTP diagnostic logging is independently selectable and metadata-only:
method, path, response status, and duration. It combines the bounded fields
into one request log and suppresses the overlapping default informational
hosting request logs. Headers and bodies are never enabled by this profile.
Authorization material, tokens, cookies, claims, configuration, secrets,
personal data, raw exception messages, and stack traces are excluded.

The OTLP endpoint is captured into generated typed Options, validated at
startup, and never treated as a secret-safe logging value. Ordinary Microsoft
logging filters may reload only from `Logging:LogLevel`. The OpenTelemetry
provider, processor,
instrumentation, sampler, and exporter graph is startup-fixed. OTLP export
uses bounded queues, batches, delays, timeouts, and drop-and-report failure
behavior. Telemetry failure never changes an application result.

Telemetry is diagnostic and may be sampled, dropped, or unavailable. It is not
a business-event ledger, security audit, compliance record, authorization
decision, guaranteed delivery mechanism, retention policy, alerting policy,
backend, collector, or dashboard.
