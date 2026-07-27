namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Startup-fixed trace sampling behavior.</summary>
public sealed record DotNetTelemetrySampling(
    [property: JsonPropertyName("kind")] DotNetTelemetrySamplerKind Kind,
    [property: JsonPropertyName("ratio")] double? Ratio);
