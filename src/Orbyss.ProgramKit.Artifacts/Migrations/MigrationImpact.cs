using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>The complete terminal assessment of one reached revision.</summary>
/// <param name="Observed">The exact observed revision.</param>
/// <param name="Target">The exact target revision.</param>
/// <param name="OwnerId">The owner of the disposition.</param>
/// <param name="Disposition">The terminal disposition.</param>
/// <param name="RequiredActions">Ordered actions required by the disposition.</param>
/// <param name="RequiredEvidence">Exact evidence needed to prove the disposition.</param>
/// <param name="CausalPaths">All retained paths from changed roots.</param>
/// <param name="Rationale">A human-reviewable rationale.</param>
public sealed record MigrationImpact(
    ArtifactReference Observed,
    ArtifactReference Target,
    ProgramKitIdentifier OwnerId,
    MigrationTerminalDisposition Disposition,
    ImmutableArray<MigrationRequiredAction> RequiredActions,
    ImmutableArray<ArtifactReference> RequiredEvidence,
    ImmutableArray<MigrationCausalPath> CausalPaths,
    string Rationale);
