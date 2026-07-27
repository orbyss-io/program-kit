namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>The execution-routing state bound to an exact static disposition.</summary>
public enum StaticConformancePlanState
{
    /// <summary>An existing compatible gate and lock must pass preflight.</summary>
    ReuseExisting,
    /// <summary>An existing gate must be extended before product work.</summary>
    ExtendExisting,
    /// <summary>A new gate must be established before product work.</summary>
    CreateNew,
    /// <summary>The exact human-accepted empty disposition permits ungated work.</summary>
    AcceptedEmpty,
    /// <summary>A required gate is unavailable; no work may execute.</summary>
    BlockedUnavailable,
}
