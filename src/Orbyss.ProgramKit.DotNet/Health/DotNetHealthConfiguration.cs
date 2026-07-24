namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Finite listener and endpoint intent for one generated host.</summary>
public sealed record DotNetHealthConfiguration(
    [property: JsonPropertyName("endpoints")] ImmutableArray<DotNetHealthEndpoint> Endpoints,
    [property: JsonPropertyName("listeners")] ImmutableArray<DotNetHealthListener> Listeners);
