namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Allocates one design invariant to its narrowest reliable layer.</summary>
public sealed record StaticInvariantAllocation(
    ProgramKitIdentifier Identity,
    string Invariant,
    StaticConformanceEnforcementLayer Layer,
    string Rationale);
