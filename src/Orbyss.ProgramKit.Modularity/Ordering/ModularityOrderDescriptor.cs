using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Modularity.Ordering;

/// <summary>
/// Defines deterministic topological constraints for one explicit registration.
/// Lower priority values win only when explicit before/after constraints leave
/// more than one registration eligible.
/// </summary>
/// <param name="Priority">The stable tie-break priority.</param>
/// <param name="Before">Registration identities that must run later.</param>
/// <param name="After">Registration identities that must run earlier.</param>
public sealed record ModularityOrderDescriptor(
    int Priority,
    ImmutableArray<ProgramKitIdentifier> Before,
    ImmutableArray<ProgramKitIdentifier> After)
{
    /// <summary>Gets the unconstrained default ordering descriptor.</summary>
    public static ModularityOrderDescriptor Default { get; } = new(0, [], []);
}
