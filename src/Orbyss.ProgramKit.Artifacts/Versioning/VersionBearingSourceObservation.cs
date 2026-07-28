namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>An exact version-bearing source observed by a bounded caller.</summary>
/// <param name="SourcePath">Normalized repository-relative source path.</param>
/// <param name="CurrentValue">Exact observed version-bearing text.</param>
/// <param name="SourceDigest">Digest of the complete observed source bytes.</param>
public sealed record VersionBearingSourceObservation(
    string SourcePath,
    string CurrentValue,
    Sha256Digest SourceDigest);
