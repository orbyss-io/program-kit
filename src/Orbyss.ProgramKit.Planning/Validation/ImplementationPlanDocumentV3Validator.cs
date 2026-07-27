using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>
/// Pure Planning 3.0 validation. It validates explicit dependency paths and
/// never infers gate ordering from sequence values, paths, or file names.
/// </summary>
public sealed class ImplementationPlanDocumentV3Validator :
    IProgramKitSemanticValidator<ImplementationPlanDocumentV3>
{
    private static readonly SemanticVersion StaticConformanceDispositionVersion =
        new("1.0.0");
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocument>
        versionTwoValidator;

    /// <summary>Initializes v3 validation over existing v2 semantics.</summary>
    public ImplementationPlanDocumentV3Validator(
        IProgramKitSemanticValidator<ImplementationPlanDocument>
            versionTwoValidator)
    {
        this.versionTwoValidator = versionTwoValidator ??
            throw new ArgumentNullException(nameof(versionTwoValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ImplementationPlanDocumentV3 value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln142,
                "A Planning 3.0 implementation plan is required.",
                "$"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        diagnostics.AddRange(versionTwoValidator.Validate(ToVersionTwo(value)).Diagnostics);
        PlanningValidation.ValidateReference(
            value.StaticConformanceDisposition,
            "$.staticConformanceDisposition",
            diagnostics);
        PlanningValidation.RequireReferenceKind(
            value.StaticConformanceDisposition,
            "static-conformance-disposition",
            "$.staticConformanceDisposition",
            diagnostics,
            PlanningDiagnosticIds.Pkpln143);
        if (value.StaticConformanceDisposition is not null &&
            value.StaticConformanceDisposition.Version !=
            StaticConformanceDispositionVersion)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln143,
                "Planning 3.0 requires static-conformance-disposition version 1.0.0.",
                "$.staticConformanceDisposition"));
        }
        if (!Enum.IsDefined(value.StaticConformanceState))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln144,
                "Static-conformance plan state must be defined.",
                "$.staticConformanceState"));
        }

        ValidateOptionalReference(
            value.GateDesign,
            "design",
            "$.gateDesign",
            diagnostics);
        ValidateOptionalPlannedArtifact(
            value.GateDefinition,
            "$.gateDefinition",
            diagnostics);
        ValidateOptionalPlannedArtifact(
            value.SelectionLock,
            "$.selectionLock",
            diagnostics);
        ValidateOptionalPlannedArtifact(
            value.ActivationEvidence,
            "$.activationEvidence",
            diagnostics);

        var units = value.WorkUnits.IsDefault
            ? ImmutableArray<PlanWorkUnitV3>.Empty
            : value.WorkUnits;
        for (var index = 0; index < units.Length; index++)
        {
            ValidateWorkUnit(units[index], index, diagnostics);
        }

        ValidateState(value, units, diagnostics);
        ValidateDependencyRoles(units, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateState(
        ImplementationPlanDocumentV3 plan,
        ImmutableArray<PlanWorkUnitV3> units,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var establishments = units
            .Where(static unit =>
                unit.WorkUnitKind == PlanWorkUnitKind.GateEstablishment)
            .ToArray();
        switch (plan.StaticConformanceState)
        {
            case StaticConformancePlanState.ReuseExisting:
                Require(establishments.Length == 0,
                    "reuse-existing cannot contain gate-establishment units.",
                    "$.workUnits",
                    diagnostics);
                RequireMaterializedGateArtifacts(plan, diagnostics);
                ValidateGatedUnits(units, diagnostics);
                break;
            case StaticConformancePlanState.ExtendExisting:
            case StaticConformancePlanState.CreateNew:
                Require(plan.GateDesign is not null,
                    "create-new and extend-existing require an exact gate design.",
                    "$.gateDesign",
                    diagnostics);
                Require(plan.GateDefinition is not null &&
                        plan.SelectionLock is not null &&
                        plan.ActivationEvidence is not null,
                    "Gate definition, selection lock, and activation evidence must be planned explicitly.",
                    "$",
                    diagnostics);
                Require(establishments.Length > 0,
                    "create-new and extend-existing require at least one gate-establishment unit.",
                    "$.workUnits",
                    diagnostics);
                ValidateEstablishmentArtifacts(plan, establishments, diagnostics);
                ValidateGatedUnits(units, diagnostics);
                break;
            case StaticConformancePlanState.AcceptedEmpty:
                Require(plan.GateDesign is null &&
                        plan.GateDefinition is null &&
                        plan.SelectionLock is null &&
                        plan.ActivationEvidence is null,
                    "The accepted-empty state cannot carry gate artifacts.",
                    "$",
                    diagnostics);
                Require(establishments.Length == 0,
                    "The accepted-empty state cannot establish a gate.",
                    "$.workUnits",
                    diagnostics);
                foreach (var unit in units)
                {
                    Require(unit.ActivationMatrix is null &&
                            unit.VerificationProfile is null,
                        "Accepted-empty work units cannot carry implicit gate activation.",
                        $"$.workUnits['{unit.WorkUnitId}']",
                        diagnostics);
                }

                break;
            case StaticConformancePlanState.BlockedUnavailable:
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln145,
                    "blocked-unavailable prevents implementation-plan execution.",
                    "$.staticConformanceState"));
                break;
        }
    }

    private static void RequireMaterializedGateArtifacts(
        ImplementationPlanDocumentV3 plan,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        Require(plan.GateDefinition?.State == PlannedArtifactState.Materialized &&
                plan.SelectionLock?.State == PlannedArtifactState.Materialized &&
                plan.ActivationEvidence?.State == PlannedArtifactState.Materialized,
            "reuse-existing requires materialized gate definition, selection lock, and activation evidence at preflight.",
            "$",
            diagnostics);
    }

    private static void ValidateGatedUnits(
        ImmutableArray<PlanWorkUnitV3> units,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var unit in units)
        {
            Require(unit.ActivationMatrix is not null,
                "Every gated work unit requires an exact activation matrix.",
                $"$.workUnits['{unit.WorkUnitId}'].activationMatrix",
                diagnostics);
            Require(unit.VerificationProfile is not null,
                "Every gated work unit requires an exact verification profile.",
                $"$.workUnits['{unit.WorkUnitId}'].verificationProfile",
                diagnostics);
        }
    }

    private static void ValidateEstablishmentArtifacts(
        ImplementationPlanDocumentV3 plan,
        IReadOnlyCollection<PlanWorkUnitV3> establishments,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var outputs = establishments
            .SelectMany(static unit => unit.Outputs.IsDefault
                ? []
                : unit.Outputs)
            .ToArray();
        foreach (var planned in new[]
                 {
                     plan.GateDefinition!,
                     plan.SelectionLock!,
                     plan.ActivationEvidence!,
                 })
        {
            Require(outputs.Contains(planned),
                $"Gate-establishment work must declare planned output '{planned.Identity.Value}@{planned.Version.Value}'.",
                "$.workUnits",
                diagnostics);
        }

        Require(establishments.Any(unit =>
                !unit.Inputs.IsDefault &&
                unit.Inputs.Contains(plan.GateDesign!)),
            "Gate-establishment work must consume the exact gate design.",
            "$.workUnits",
            diagnostics);
    }

    private static void ValidateDependencyRoles(
        ImmutableArray<PlanWorkUnitV3> units,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var byId = units
            .Where(static unit => !string.IsNullOrWhiteSpace(unit.WorkUnitId))
            .GroupBy(static unit => unit.WorkUnitId, StringComparer.Ordinal)
            .ToDictionary(
                static group => group.Key,
                static group => group.First(),
                StringComparer.Ordinal);
        var establishments = units
            .Where(static unit =>
                unit.WorkUnitKind == PlanWorkUnitKind.GateEstablishment)
            .Select(static unit => unit.WorkUnitId)
            .ToArray();
        var products = units
            .Where(static unit => unit.WorkUnitKind == PlanWorkUnitKind.Product)
            .Select(static unit => unit.WorkUnitId)
            .ToArray();

        foreach (var unit in units)
        {
            if (unit.WorkUnitKind is PlanWorkUnitKind.Product
                or PlanWorkUnitKind.Closure)
            {
                foreach (var establishment in establishments)
                {
                    Require(IsReachable(unit.WorkUnitId, establishment, byId, []),
                        $"Work unit '{unit.WorkUnitId}' must depend explicitly or transitively on gate-establishment unit '{establishment}'.",
                        $"$.workUnits['{unit.WorkUnitId}'].dependsOn",
                        diagnostics);
                }
            }

            if (unit.WorkUnitKind == PlanWorkUnitKind.Closure)
            {
                foreach (var product in products)
                {
                    Require(IsReachable(unit.WorkUnitId, product, byId, []),
                        $"Closure work unit '{unit.WorkUnitId}' must depend explicitly or transitively on product unit '{product}'.",
                        $"$.workUnits['{unit.WorkUnitId}'].dependsOn",
                        diagnostics);
                }
            }
        }
    }

    private static bool IsReachable(
        string sourceId,
        string targetId,
        IReadOnlyDictionary<string, PlanWorkUnitV3> byId,
        HashSet<string> visited)
    {
        if (!visited.Add(sourceId) ||
            !byId.TryGetValue(sourceId, out var source) ||
            source.DependsOn.IsDefault)
        {
            return false;
        }

        return source.DependsOn.Any(dependency =>
            string.Equals(dependency, targetId, StringComparison.Ordinal) ||
            IsReachable(dependency, targetId, byId, visited));
    }

    private static void ValidateWorkUnit(
        PlanWorkUnitV3 unit,
        int index,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var path = $"$.workUnits[{index}]";
        if (!Enum.IsDefined(unit.WorkUnitKind))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln146,
                "Work-unit kind must be defined.",
                $"{path}.workUnitKind"));
        }

        ValidateOptionalReference(
            unit.ActivationMatrix,
            "activation-matrix",
            $"{path}.activationMatrix",
            diagnostics);
        ValidateOptionalReference(
            unit.VerificationProfile,
            "profile",
            $"{path}.verificationProfile",
            diagnostics);
    }

    private static void ValidateOptionalReference(
        ArtifactReference? value,
        string kind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            return;
        }

        PlanningValidation.ValidateReference(value, path, diagnostics);
        PlanningValidation.RequireReferenceKind(
            value,
            kind,
            path,
            diagnostics,
            PlanningDiagnosticIds.Pkpln147);
    }

    private static void ValidateOptionalPlannedArtifact(
        PlannedArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            return;
        }

        PlanningValidation.ValidatePlannedArtifacts([value], path, diagnostics);
    }

    private static ImplementationPlanDocument ToVersionTwo(
        ImplementationPlanDocumentV3 value) =>
        new(
            value.Design,
            value.OwnerId,
            value.State,
            value.RequirementIds,
            value.WorkUnits.Select(ToVersionTwo).ToImmutableArray(),
            value.ParallelGroups,
            value.Trace,
            value.UnresolvedDecisions);

    private static PlanWorkUnit ToVersionTwo(PlanWorkUnitV3 value) =>
        new(
            value.WorkUnitId,
            value.RequiredOutcome,
            value.Sequence,
            value.ParallelGroupId,
            value.DependsOn,
            value.Inputs,
            value.Outputs,
            value.AllowedEdits,
            value.SourceDependencies,
            value.ExternalDependencies,
            value.Migrations,
            value.Compatibility,
            value.StopConditions,
            value.Verification,
            value.SelectedTests);

    private static void Require(
        bool condition,
        string message,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!condition)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln148,
                message,
                path));
        }
    }
}
