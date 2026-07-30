using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Adds the exact schema identity while preserving every plan value.</summary>
public static class ImplementationPlanAlpha3ToAlpha4Migration
{
    /// <summary>Creates the current writer with exact migrated design-flow references.</summary>
    public static ImplementationPlanDocumentAlpha4 Migrate(
        ImplementationPlanDocumentAlpha3 source,
        ArtifactReference suppliedAlpha3Design,
        ArtifactReference suppliedAlpha2Disposition)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedAlpha3Design);
        ArgumentNullException.ThrowIfNull(suppliedAlpha2Disposition);
        return new ImplementationPlanDocumentAlpha4(
            ImplementationPlanDocumentAlpha4.SchemaUri,
            suppliedAlpha3Design,
            source.OwnerId,
            source.State,
            source.RequirementIds,
            source.WorkUnits,
            source.ParallelGroups,
            source.Trace,
            source.UnresolvedDecisions,
            suppliedAlpha2Disposition,
            source.StaticConformanceState,
            source.GateDesign,
            source.GateDefinition,
            source.SelectionLock,
            source.ActivationEvidence);
    }

    internal static ImplementationPlanDocumentAlpha3 ToAlpha3Shape(
        ImplementationPlanDocumentAlpha4 source) =>
        new(
            source.Design,
            source.OwnerId,
            source.State,
            source.RequirementIds,
            source.WorkUnits,
            source.ParallelGroups,
            source.Trace,
            source.UnresolvedDecisions,
            source.StaticConformanceDisposition,
            source.StaticConformanceState,
            source.GateDesign,
            source.GateDefinition,
            source.SelectionLock,
            source.ActivationEvidence);
}
