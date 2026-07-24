namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>One exact package in a generated host dependency closure.</summary>
public sealed record DotNetPackageLock(
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("packageDigest")] Sha256Digest PackageDigest);
