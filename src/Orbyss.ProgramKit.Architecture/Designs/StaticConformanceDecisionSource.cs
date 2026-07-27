namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Identifies the exact human instruction that selected a disposition candidate.
/// It is evidence of the decision source, not architecture approval.
/// </summary>
public sealed record StaticConformanceDecisionSource(
    ArtifactReference Source,
    string JsonPointer);
