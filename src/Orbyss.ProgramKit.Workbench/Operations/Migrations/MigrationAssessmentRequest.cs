namespace Orbyss.ProgramKit.Workbench.Operations.Migrations;

/// <summary>Explicit immutable inputs to one migration impact assessment.</summary>
/// <param name="VersionMapReference">Exact map revision used as input.</param>
/// <param name="VersionSelectionReference">Exact selection revision used as input.</param>
/// <param name="VersionMap">Typed map content.</param>
/// <param name="VersionSelection">Observed and human-selected exact targets.</param>
/// <param name="Decisions">One complete decision per reached semantic identity.</param>
/// <param name="Limits">Finite closure limits.</param>
public sealed record MigrationAssessmentRequest(
    ArtifactReference VersionMapReference,
    ArtifactReference VersionSelectionReference,
    VersionMapDocument VersionMap,
    VersionSelectionDocument VersionSelection,
    ImmutableArray<MigrationBoundaryDecision> Decisions,
    MigrationAnalysisLimits Limits);
