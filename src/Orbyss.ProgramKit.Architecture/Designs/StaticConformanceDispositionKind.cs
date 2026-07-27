namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>The explicit static-conformance decision for one software design.</summary>
public enum StaticConformanceDispositionKind
{
    /// <summary>Use one or more existing compatible consumer-owned gates.</summary>
    ReuseExisting,
    /// <summary>Extend an existing consumer-owned gate under a linked gate design.</summary>
    ExtendExisting,
    /// <summary>Create a consumer-owned gate under a linked gate design.</summary>
    CreateNew,
    /// <summary>No static gate is justified and the exact empty choice was accepted.</summary>
    NotJustified,
    /// <summary>A required gate is unavailable, so implementation is blocked.</summary>
    BlockedUnavailable,
}
