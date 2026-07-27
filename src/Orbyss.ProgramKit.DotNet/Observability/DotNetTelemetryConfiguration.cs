using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Exact logging, tracing, metrics, correlation, and export mechanics for one host.</summary>
public sealed record DotNetTelemetryConfiguration(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("specificationRevision")] ArtifactReference SpecificationRevision,
    [property: JsonPropertyName("semanticConventionRevision")] ArtifactReference SemanticConventionRevision,
    [property: JsonPropertyName("packages")] ImmutableArray<DotNetPackageReference> Packages,
    [property: JsonPropertyName("resource")] DotNetTelemetryResource Resource,
    [property: JsonPropertyName("loggerEvents")] ImmutableArray<DotNetLoggerEvent> LoggerEvents,
    [property: JsonPropertyName("activities")] ImmutableArray<DotNetActivityDefinition> Activities,
    [property: JsonPropertyName("metrics")] ImmutableArray<DotNetMetricDefinition> Metrics,
    [property: JsonPropertyName("instrumentations")] ImmutableArray<DotNetTelemetryInstrumentation> Instrumentations,
    [property: JsonPropertyName("sampling")] DotNetTelemetrySampling Sampling,
    [property: JsonPropertyName("otlpExporter")] DotNetOtlpExporter? OtlpExporter,
    [property: JsonPropertyName("httpDiagnostics")] DotNetHttpDiagnosticProfile HttpDiagnostics,
    [property: JsonPropertyName("baggageAllowList")] ImmutableArray<string> BaggageAllowList,
    [property: JsonPropertyName("loggingFilterConfigurationKey")] string? LoggingFilterConfigurationKey,
    [property: JsonPropertyName("providerGraphReloadable")] bool ProviderGraphReloadable,
    [property: JsonPropertyName("shutdownTimeoutMilliseconds")] int ShutdownTimeoutMilliseconds);
