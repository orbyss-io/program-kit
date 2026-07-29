namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>One exact managed reference in a materialized compiler closure.</summary>
public sealed record DotNetConsoleMaterializedReference(
    [property: JsonPropertyName("assemblyIdentity")] string AssemblyIdentity,
    [property: JsonPropertyName("revision")] ArtifactReference Revision,
    [property: JsonPropertyName("relativePath")] string RelativePath,
    [property: JsonPropertyName("consumer")] bool Consumer);
