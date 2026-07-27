namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>One explicit low-level AppHost resource.</summary>
public sealed record AspireResourceDefinition(
    string Name,
    AspireResourceKind Kind,
    string? ProjectPath,
    string? ProjectMetadataTypeName,
    string? ExecutablePath,
    string? WorkingDirectory,
    ImmutableArray<string> Arguments,
    string? ContainerImage);
