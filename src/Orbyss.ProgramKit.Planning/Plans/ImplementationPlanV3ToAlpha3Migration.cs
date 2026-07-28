using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Deterministically migrates Planning 3.0 to Implementation Plan alpha
/// revision 3.
/// </summary>
public static class ImplementationPlanV3ToAlpha3Migration
{
    /// <summary>
    /// Preserves every Planning 3.0 field while replacing only the exact
    /// migrated design and static-conformance disposition references.
    /// </summary>
    public static ImplementationPlanDocumentAlpha3 Migrate(
        ImplementationPlanDocumentV3 source,
        ArtifactReference suppliedAlphaDesign,
        ArtifactReference suppliedAlphaDisposition)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedAlphaDesign);
        ArgumentNullException.ThrowIfNull(suppliedAlphaDisposition);
        return new ImplementationPlanDocumentAlpha3(
            suppliedAlphaDesign,
            source.OwnerId,
            source.State,
            source.RequirementIds,
            source.WorkUnits,
            source.ParallelGroups,
            source.Trace,
            source.UnresolvedDecisions,
            suppliedAlphaDisposition,
            source.StaticConformanceState,
            source.GateDesign,
            source.GateDefinition,
            source.SelectionLock,
            source.ActivationEvidence);
    }

    internal static ImplementationPlanDocumentV3 ToLegacyShape(
        ImplementationPlanDocumentAlpha3 source) =>
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
