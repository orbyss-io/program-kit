namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Explicit Healthy, Degraded, and Unhealthy HTTP status mapping.</summary>
public sealed record DotNetHealthStatusCodeMap(
    [property: JsonPropertyName("healthy")] int Healthy,
    [property: JsonPropertyName("degraded")] int Degraded,
    [property: JsonPropertyName("unhealthy")] int Unhealthy);
