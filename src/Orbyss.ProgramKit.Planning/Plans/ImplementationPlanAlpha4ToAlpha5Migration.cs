using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Migrates alpha.4 only when every work unit receives explicit binding
/// semantics. The migration never guesses an execution-resolution policy.
/// </summary>
public static class ImplementationPlanAlpha4ToAlpha5Migration
{
    /// <summary>Creates alpha.5 without changing any approved plan obligation.</summary>
    public static ImplementationPlanDocumentAlpha5 Migrate(
        ImplementationPlanDocumentAlpha4 source,
        ImmutableArray<PlanWorkUnitAlpha5Binding> suppliedBindings)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (suppliedBindings.IsDefault)
        {
            throw new ArgumentException(
                "Explicit alpha.5 work-unit bindings are required.",
                nameof(suppliedBindings));
        }

        var bindingsById = suppliedBindings
            .GroupBy(static binding => binding.WorkUnitId, StringComparer.Ordinal)
            .ToDictionary(
                static group => group.Key,
                static group => group.ToArray(),
                StringComparer.Ordinal);
        var sourceIds = source.WorkUnits
            .Select(static unit => unit.WorkUnitId)
            .ToHashSet(StringComparer.Ordinal);
        if (bindingsById.Count != source.WorkUnits.Length ||
            bindingsById.Any(static pair => pair.Value.Length != 1) ||
            bindingsById.Keys.Any(id => !sourceIds.Contains(id)) ||
            sourceIds.Any(id => !bindingsById.ContainsKey(id)))
        {
            throw new ArgumentException(
                "Exactly one explicit alpha.5 binding is required for every source work unit and no other ID.",
                nameof(suppliedBindings));
        }

        return new ImplementationPlanDocumentAlpha5(
            ImplementationPlanDocumentAlpha5.SchemaUri,
            source.Design,
            source.OwnerId,
            source.State,
            source.RequirementIds,
            source.WorkUnits
                .Select(unit => MigrateUnit(
                    unit,
                    bindingsById[unit.WorkUnitId][0]))
                .ToImmutableArray(),
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

    internal static ImplementationPlanDocumentAlpha4 ToAlpha4Shape(
        ImplementationPlanDocumentAlpha5 source) =>
        new(
            ImplementationPlanDocumentAlpha4.SchemaUri,
            source.Design,
            source.OwnerId,
            source.State,
            source.RequirementIds,
            source.WorkUnits
                .Select(ToAlpha4Shape)
                .ToImmutableArray(),
            source.ParallelGroups,
            source.Trace,
            source.UnresolvedDecisions,
            source.StaticConformanceDisposition,
            source.StaticConformanceState,
            source.GateDesign,
            source.GateDefinition,
            source.SelectionLock,
            source.ActivationEvidence);

    private static PlanWorkUnitAlpha5 MigrateUnit(
        PlanWorkUnitV3 source,
        PlanWorkUnitAlpha5Binding binding) =>
        new(
            source.WorkUnitId,
            source.RequiredOutcome,
            source.Sequence,
            source.ParallelGroupId,
            source.DependsOn,
            source.Inputs,
            source.Outputs,
            source.AllowedEdits,
            source.SourceDependencies,
            source.ExternalDependencies,
            source.Migrations,
            source.Compatibility,
            source.StopConditions,
            source.Verification,
            source.SelectedTests,
            source.WorkUnitKind,
            binding.ActivationMatrix,
            binding.VerificationProfile);

    private static PlanWorkUnitV3 ToAlpha4Shape(PlanWorkUnitAlpha5 source) =>
        new(
            source.WorkUnitId,
            source.RequiredOutcome,
            source.Sequence,
            source.ParallelGroupId,
            source.DependsOn,
            source.Inputs,
            source.Outputs,
            source.AllowedEdits,
            source.SourceDependencies,
            source.ExternalDependencies,
            source.Migrations,
            source.Compatibility,
            source.StopConditions,
            source.Verification,
            source.SelectedTests,
            source.WorkUnitKind,
            source.ActivationMatrix?.ApprovedArtifact,
            source.VerificationProfile?.ApprovedArtifact);
}
