using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Pure admission classification for the existing plan execution authority.
/// This type does not execute work, mutate plans, or grant authority.
/// </summary>
public sealed class ImplementationPlanV3AdmissionEvaluator
{
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocumentV3>
        validator;

    /// <summary>Initializes classification with exact v3 semantic validation.</summary>
    public ImplementationPlanV3AdmissionEvaluator(
        IProgramKitSemanticValidator<ImplementationPlanDocumentV3> validator)
    {
        this.validator = validator ??
            throw new ArgumentNullException(nameof(validator));
    }

    /// <summary>Classifies only dependency-ready work under exact evidence.</summary>
    public PlanWorkUnitAdmission Evaluate(
        ImplementationPlanDocumentV3 plan,
        ImmutableArray<string> completedWorkUnitIds,
        StaticConformanceDispositionSnapshot? disposition,
        StaticConformanceExecutionSnapshot? snapshot)
    {
        var validation = validator.Validate(plan);
        if (!validation.IsValid)
        {
            return new PlanWorkUnitAdmission(
                [],
                validation.Diagnostics.Select(static diagnostic =>
                    string.Concat(
                        diagnostic.Id,
                        " ",
                        diagnostic.Path,
                        ": ",
                        diagnostic.Message))
                    .ToImmutableArray());
        }

        return EvaluateValidated(
            plan,
            completedWorkUnitIds,
            disposition,
            snapshot);
    }

    internal static PlanWorkUnitAdmission EvaluateValidated(
        ImplementationPlanDocumentV3 plan,
        ImmutableArray<string> completedWorkUnitIds,
        StaticConformanceDispositionSnapshot? disposition,
        StaticConformanceExecutionSnapshot? snapshot)
    {
        if (!DispositionIsCompatible(plan, disposition))
        {
            return new PlanWorkUnitAdmission(
                [],
                ["The exact validated static-conformance disposition and its state must match the implementation plan before any work is admissible."]);
        }

        var completed = completedWorkUnitIds.IsDefault
            ? new HashSet<string>(StringComparer.Ordinal)
            : completedWorkUnitIds.ToHashSet(StringComparer.Ordinal);
        var ready = plan.WorkUnits
            .Where(unit =>
                !completed.Contains(unit.WorkUnitId) &&
                unit.DependsOn.All(completed.Contains))
            .ToArray();

        if (plan.StaticConformanceState ==
            StaticConformancePlanState.AcceptedEmpty)
        {
            return new PlanWorkUnitAdmission(
                ready.Select(static unit => unit.WorkUnitId).ToImmutableArray(),
                []);
        }

        if (!SnapshotIsCompatible(plan, snapshot))
        {
            if (plan.StaticConformanceState is
                StaticConformancePlanState.CreateNew or
                StaticConformancePlanState.ExtendExisting)
            {
                return new PlanWorkUnitAdmission(
                    ready.Where(static unit =>
                            unit.WorkUnitKind ==
                            PlanWorkUnitKind.GateEstablishment)
                        .Select(static unit => unit.WorkUnitId)
                        .ToImmutableArray(),
                    ["Compatible gate activation evidence is not available; only dependency-ready gate-establishment work is admissible."]);
            }

            return new PlanWorkUnitAdmission(
                [],
                ["A compatible materialized selection lock and activation evidence are required at preflight."]);
        }

        return new PlanWorkUnitAdmission(
            ready.Select(static unit => unit.WorkUnitId).ToImmutableArray(),
            []);
    }

    private static bool DispositionIsCompatible(
        ImplementationPlanDocumentV3 plan,
        StaticConformanceDispositionSnapshot? snapshot) =>
        snapshot is not null &&
        plan.StaticConformanceDisposition == snapshot.Disposition &&
        plan.StaticConformanceState == snapshot.State;

    private static bool SnapshotIsCompatible(
        ImplementationPlanDocumentV3 plan,
        StaticConformanceExecutionSnapshot? snapshot)
    {
        if (snapshot is null ||
            plan.SelectionLock is null ||
            plan.ActivationEvidence is null ||
            !Matches(plan.SelectionLock, snapshot.SelectionLock) ||
            !Matches(plan.ActivationEvidence, snapshot.ActivationEvidence))
        {
            return false;
        }

        var matrices = snapshot.ActivationMatrices.IsDefault
            ? []
            : snapshot.ActivationMatrices.ToHashSet();
        var profiles = snapshot.VerificationProfiles.IsDefault
            ? []
            : snapshot.VerificationProfiles.ToHashSet();
        return plan.WorkUnits.All(unit =>
            unit.ActivationMatrix is not null &&
            matrices.Contains(unit.ActivationMatrix) &&
            unit.VerificationProfile is not null &&
            profiles.Contains(unit.VerificationProfile));
    }

    private static bool Matches(
        PlannedArtifactReference planned,
        ArtifactReference observed) =>
        planned.Identity == observed.Identity &&
        planned.Version == observed.Version &&
        (planned.State == PlannedArtifactState.Prospective ||
         planned.IntegrityDigest == observed.Digest);
}
