namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>One normalized payload path and its exact bytes.</summary>
public sealed record GeneratedOutputManifestEntry(
    [property: JsonPropertyName("path")] string Path,
    [property: JsonPropertyName("sha256")] string Sha256,
    [property: JsonPropertyName("length")] long Length);
