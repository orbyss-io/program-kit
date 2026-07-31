using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>A binding receipt or the finite reasons resolution failed closed.</summary>
public sealed record PlanArtifactBindingResolution(
    PlanArtifactBindingReceipt? Receipt,
    ImmutableArray<string> BlockingReasons)
{
    /// <summary>Gets whether one exact receipt was produced.</summary>
    public bool IsResolved =>
        Receipt is not null &&
        (BlockingReasons.IsDefaultOrEmpty || BlockingReasons.Length == 0);
}
