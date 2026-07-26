namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>One explicit service-discovery reference between resources.</summary>
public sealed record AspireResourceReference(
    string SourceResourceName,
    string TargetResourceName,
    string TargetEndpointName);
