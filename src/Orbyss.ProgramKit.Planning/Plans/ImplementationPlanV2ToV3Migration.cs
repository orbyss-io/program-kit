using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Deterministic Planning 2.0 to 3.0 migration.</summary>
public static class ImplementationPlanV2ToV3Migration
{
    /// <summary>
    /// Migrates only from the supplied explicit human decisions; missing,
    /// duplicate, or extra work-unit classifications fail closed.
    /// </summary>
    public static ImplementationPlanDocumentV3 Migrate(
        ImplementationPlanDocument source,
        ImplementationPlanV3MigrationInput supplied)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(supplied);
        ArgumentNullException.ThrowIfNull(supplied.StaticConformanceDisposition);
        if (supplied.WorkUnitBindings.IsDefault)
        {
            throw new ArgumentException(
                "Every v2 work unit requires an explicit v3 binding.",
                nameof(supplied));
        }

        var bindings = supplied.WorkUnitBindings.ToDictionary(
            static binding => binding.WorkUnitId,
            StringComparer.Ordinal);
        if (bindings.Count != supplied.WorkUnitBindings.Length ||
            bindings.Count != source.WorkUnits.Length ||
            source.WorkUnits.Any(unit => !bindings.ContainsKey(unit.WorkUnitId)))
        {
            throw new ArgumentException(
                "Work-unit bindings must match the v2 work-unit identities exactly.",
                nameof(supplied));
        }

        var workUnits = source.WorkUnits.Select(unit =>
        {
            var binding = bindings[unit.WorkUnitId];
            return new PlanWorkUnitV3(
                unit.WorkUnitId,
                unit.RequiredOutcome,
                unit.Sequence,
                unit.ParallelGroupId,
                unit.DependsOn,
                unit.Inputs,
                unit.Outputs,
                unit.AllowedEdits,
                unit.SourceDependencies,
                unit.ExternalDependencies,
                unit.Migrations,
                unit.Compatibility,
                unit.StopConditions,
                unit.Verification,
                unit.SelectedTests,
                binding.WorkUnitKind,
                binding.ActivationMatrix,
                binding.VerificationProfile);
        }).ToImmutableArray();

        return new ImplementationPlanDocumentV3(
            source.Design,
            source.OwnerId,
            source.State,
            source.RequirementIds,
            workUnits,
            source.ParallelGroups,
            source.Trace,
            source.UnresolvedDecisions,
            supplied.StaticConformanceDisposition,
            supplied.StaticConformanceState,
            supplied.GateDesign,
            supplied.GateDefinition,
            supplied.SelectionLock,
            supplied.ActivationEvidence);
    }
}
