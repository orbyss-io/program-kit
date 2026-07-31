# .NET shell telemetry v4 to v5

This source-guidance migration adds explicit diagnostics and telemetry
composition without inventing application observability meaning.

For each v4 host:

1. Add `telemetry: null` when the host has no reviewed telemetry selection.
   This preserves behavior and emits no telemetry.
2. To enable telemetry, supply an owner-reviewed v5 composition with exact
   OpenTelemetry specification, HTTP semantic-convention, profile, and package
   revisions.
3. Map operation signal meaning only from existing Operations declarations.
   DotNet owns logger, activity, meter, instrumentation, and exporter mechanics;
   it does not create business-event or audit meaning.
4. Use unique typed logger categories, event IDs and names; bounded correlation
   scopes; internal/producer/consumer custom activities; stable
   meter/instrument names; explicit units; and finite, non-sensitive attribute
   value catalogs.
5. Select ASP.NET Core and HttpClient instrumentation at most once. Never add
   custom HTTP server/client spans beside the selected framework
   instrumentation.
6. Keep HTTP diagnostics metadata-only. Headers, bodies, authorization
   material, tokens, cookies, claims, configuration, secrets, personal data,
   raw exception messages, and stack traces remain excluded.
7. Keep the provider, processor, instrumentation, and exporter graph
   startup-fixed. Bind the OTLP endpoint through generated startup-validated
   Options. Only ordinary Microsoft logging filters may reload from
   `Logging:LogLevel`.
8. Treat exporter failure as bounded diagnostic loss. It cannot change the
   application result or become an audit, authorization, compliance, or
   business-event channel.

The initial exact adapter uses OpenTelemetry .NET 1.17.0, OpenTelemetry
Specification 1.55.0, and the stable HTTP semantic conventions implemented by
the selected ASP.NET Core and HttpClient instrumentation. No unstable
semantic-convention group is enabled implicitly.
