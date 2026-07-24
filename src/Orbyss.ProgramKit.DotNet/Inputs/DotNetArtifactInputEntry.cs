namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>One exact artifact revision mapped to a normalized relative input path.</summary>
public sealed record DotNetArtifactInputEntry(
    [property: JsonPropertyName("revision")] ArtifactReference Revision,
    [property: JsonPropertyName("relativePath")] string RelativePath);
