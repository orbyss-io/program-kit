namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Adds the exact schema identity while preserving every disposition value.</summary>
public static class StaticConformanceDispositionAlpha1ToAlpha2Migration
{
    /// <summary>Creates the current writer and selects the supplied alpha.3 design.</summary>
    public static StaticConformanceDispositionAlpha2 Migrate(
        StaticConformanceDispositionAlpha1 source,
        ArtifactReference suppliedAlpha3Design)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedAlpha3Design);
        return new StaticConformanceDispositionAlpha2(
            StaticConformanceDispositionAlpha2.SchemaUri,
            suppliedAlpha3Design,
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

    internal static StaticConformanceDispositionAlpha1 ToAlpha1Shape(
        StaticConformanceDispositionAlpha2 source) =>
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
