namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Immutable entry shape from inventory contract 0.1.0-alpha.1.</summary>
public sealed record VersionIntentInventoryEntryAlpha1(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string SourcePath,
    string CurrentValue,
    Sha256Digest SourceDigest,
    VersionIntent Intent,
    bool IsActive,
    int? OwnedRevisionOrdinal,
    VersionTransitionDispositionAlpha1 TransitionDisposition);
