namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Classifies one exact repository version-bearing source.</summary>
/// <param name="Identity">Stable semantic identity represented by the source.</param>
/// <param name="OwnerId">Semantic owner of the version decision.</param>
/// <param name="SourcePath">Normalized repository-relative source path.</param>
/// <param name="SourceLocator">Stable locator of the value within the source file.</param>
/// <param name="CurrentValue">Exact current version-bearing text.</param>
/// <param name="SourceDigest">Digest of the complete source file bytes.</param>
/// <param name="Intent">Explicit version intent.</param>
/// <param name="IsActive">Whether the source participates in current selection.</param>
/// <param name="OwnedRevisionOrdinal">One-based revision ordinal for owned artifacts.</param>
/// <param name="TransitionDisposition">Explicit transition treatment.</param>
public sealed record VersionIntentInventoryEntry(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string SourcePath,
    string SourceLocator,
    string CurrentValue,
    Sha256Digest SourceDigest,
    VersionIntent Intent,
    bool IsActive,
    int? OwnedRevisionOrdinal,
    VersionTransitionDisposition TransitionDisposition);
