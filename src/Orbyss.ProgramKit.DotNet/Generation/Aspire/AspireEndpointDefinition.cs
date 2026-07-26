namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>One explicit resource endpoint.</summary>
public sealed record AspireEndpointDefinition(
    string ResourceName,
    string Name,
    string Scheme,
    int TargetPort,
    int? HostPort,
    bool IsExternal,
    bool IsProxied);
