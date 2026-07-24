namespace Orbyss.ProgramKit.DotNet.Packages;

/// <summary>Exact package identity, version, and immutable package digest.</summary>
public sealed record DotNetPackageReference(
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("sha256")] Sha256Digest Sha256);
