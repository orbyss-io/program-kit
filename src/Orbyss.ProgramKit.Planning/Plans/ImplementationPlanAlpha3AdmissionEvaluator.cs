using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Pure dependency-ready admission for Implementation Plan
/// 0.1.0-alpha.3.
/// </summary>
public sealed class ImplementationPlanAlpha3AdmissionEvaluator
{
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocumentAlpha3>
        validator;

    /// <summary>Initializes alpha admission with exact semantic validation.</summary>
    public ImplementationPlanAlpha3AdmissionEvaluator(
        IProgramKitSemanticValidator<ImplementationPlanDocumentAlpha3>
            validator)
    {
        this.validator = validator ??
            throw new ArgumentNullException(nameof(validator));
    }

    /// <summary>Classifies only dependency-ready work under exact evidence.</summary>
    public PlanWorkUnitAdmission Evaluate(
        ImplementationPlanDocumentAlpha3 plan,
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

        return ImplementationPlanV3AdmissionEvaluator.EvaluateValidated(
            ImplementationPlanV3ToAlpha3Migration.ToLegacyShape(plan),
            completedWorkUnitIds,
            disposition,
            snapshot);
    }
}
