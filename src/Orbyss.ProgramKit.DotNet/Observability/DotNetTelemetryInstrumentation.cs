namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>One exact framework instrumentation selection.</summary>
public sealed record DotNetTelemetryInstrumentation(
    [property: JsonPropertyName("kind")] DotNetTelemetryInstrumentationKind Kind,
    [property: JsonPropertyName("traces")] bool Traces,
    [property: JsonPropertyName("metrics")] bool Metrics,
    [property: JsonPropertyName("recordExceptions")] bool RecordExceptions);
