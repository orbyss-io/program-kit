using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A truthful implementation status claim with inspectable evidence.</summary>
public sealed record ArchitectureStatusClaim(
    ProgramKitIdentifier SubjectId,
    ArtifactStatus Status,
    ImmutableArray<ArtifactReference> Evidence,
    string Claim);
