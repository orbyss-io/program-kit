namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Exact digest inventory for every payload file in one generated root.</summary>
public sealed record GeneratedOutputManifest(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("formatVersion")] string FormatVersion,
    [property: JsonPropertyName("ownership")] string Ownership,
    [property: JsonPropertyName("files")]
    ImmutableArray<GeneratedOutputManifestEntry> Files);
