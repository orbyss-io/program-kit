namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>One exact consumer-owned artifact copied into the input closure.</summary>
public sealed record DotNetConsoleSuppliedArtifact(
    [property: JsonPropertyName("revision")] ArtifactReference Revision,
    [property: JsonPropertyName("workspaceRelativePath")]
    string WorkspaceRelativePath,
    [property: JsonPropertyName("outputRelativePath")]
    string OutputRelativePath);
