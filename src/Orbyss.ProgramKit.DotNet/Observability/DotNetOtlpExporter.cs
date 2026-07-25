namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Exact bounded OTLP exporter selection; the endpoint remains configuration-owned.</summary>
public sealed record DotNetOtlpExporter(
    [property: JsonPropertyName("endpointConfigurationKey")] string EndpointConfigurationKey,
    [property: JsonPropertyName("protocol")] DotNetOtlpProtocol Protocol,
    [property: JsonPropertyName("maxQueueSize")] int MaxQueueSize,
    [property: JsonPropertyName("maxExportBatchSize")] int MaxExportBatchSize,
    [property: JsonPropertyName("scheduledDelayMilliseconds")] int ScheduledDelayMilliseconds,
    [property: JsonPropertyName("exportTimeoutMilliseconds")] int ExportTimeoutMilliseconds,
    [property: JsonPropertyName("failureDisposition")] DotNetTelemetryFailureDisposition FailureDisposition);
