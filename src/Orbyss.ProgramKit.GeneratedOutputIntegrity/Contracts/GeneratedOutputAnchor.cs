namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Sibling seal over the exact in-root manifest bytes.</summary>
public sealed record GeneratedOutputAnchor(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("formatVersion")] string FormatVersion,
    [property: JsonPropertyName("manifestPath")] string ManifestPath,
    [property: JsonPropertyName("manifestSha256")] string ManifestSha256);
