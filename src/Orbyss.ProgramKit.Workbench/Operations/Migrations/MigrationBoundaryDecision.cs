namespace Orbyss.ProgramKit.Workbench.Operations.Migrations;

/// <summary>Human-owned terminal decision for one reached semantic identity.</summary>
/// <param name="Identity">Reached boundary identity.</param>
/// <param name="CompatibilityClaims">Complete independent compatibility classification.</param>
/// <param name="Disposition">Exactly one terminal disposition.</param>
/// <param name="RequiredActions">Ordered actions required by the disposition.</param>
/// <param name="RequiredEvidence">Exact evidence proving the decision.</param>
/// <param name="Rationale">Human-reviewable rationale.</param>
public sealed record MigrationBoundaryDecision(
    ProgramKitIdentifier Identity,
    ImmutableArray<CompatibilityClaim> CompatibilityClaims,
    MigrationTerminalDisposition Disposition,
    ImmutableArray<MigrationRequiredAction> RequiredActions,
    ImmutableArray<ArtifactReference> RequiredEvidence,
    string Rationale);
