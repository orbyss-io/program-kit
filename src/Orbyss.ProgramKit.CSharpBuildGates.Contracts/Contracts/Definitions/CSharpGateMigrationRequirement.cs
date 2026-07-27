using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>An explicit migration boundary; migration is never inferred.</summary>
public sealed record CSharpGateMigrationRequirement(
    ArtifactReference Source,
    ArtifactReference Target,
    ArtifactReference Guidance,
    bool RejectsLoss,
    bool IsDeterministic,
    bool IsIdempotent);
