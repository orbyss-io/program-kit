namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Deterministically migrates a legacy static-conformance disposition to its
/// first alpha revision.
/// </summary>
public static class StaticConformanceDispositionV1ToAlpha1Migration
{
    /// <summary>
    /// Preserves every decision field while replacing only the exact migrated
    /// software-design reference supplied by the caller.
    /// </summary>
    public static StaticConformanceDispositionAlpha1 Migrate(
        StaticConformanceDisposition source,
        ArtifactReference suppliedAlphaDesign)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedAlphaDesign);
        return new StaticConformanceDispositionAlpha1(
            suppliedAlphaDesign,
            source.InvariantAllocations,
            source.Disposition,
            source.GateSelections,
            source.LinkedGateDesigns,
            source.Rationale,
            source.ResidualRisks,
            source.NonStaticClaims,
            source.DecisionSource,
            source.EmptySelectionAcceptance,
            source.Blockers);
    }

    internal static StaticConformanceDisposition ToLegacyShape(
        StaticConformanceDispositionAlpha1 source) =>
        new(
            source.SoftwareDesign,
            source.InvariantAllocations,
            source.Disposition,
            source.GateSelections,
            source.LinkedGateDesigns,
            source.Rationale,
            source.ResidualRisks,
            source.NonStaticClaims,
            source.DecisionSource,
            source.EmptySelectionAcceptance,
            source.Blockers);
}
