using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>
/// Validates Implementation Plan 0.1.0-alpha.3 with the exact alpha
/// static-conformance contract.
/// </summary>
public sealed class ImplementationPlanDocumentAlpha3Validator :
    IProgramKitSemanticValidator<ImplementationPlanDocumentAlpha3>
{
    private static readonly SemanticVersion AlphaDesignVersion =
        new("0.1.0-alpha.2");
    private static readonly SemanticVersion AlphaDispositionVersion =
        new("0.1.0-alpha.1");
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocument>
        versionTwoValidator;

    /// <summary>Initializes alpha validation over existing v2 semantics.</summary>
    public ImplementationPlanDocumentAlpha3Validator(
        IProgramKitSemanticValidator<ImplementationPlanDocument>
            versionTwoValidator)
    {
        this.versionTwoValidator = versionTwoValidator ??
            throw new ArgumentNullException(nameof(versionTwoValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        ImplementationPlanDocumentAlpha3 value)
    {
        var diagnostics =
            System.Collections.Immutable.ImmutableArray
                .CreateBuilder<
                    Orbyss.ProgramKit.Artifacts.Diagnostics.ProgramKitDiagnostic>();
        diagnostics.AddRange(
            ImplementationPlanDocumentV3Validator.ValidateVersioned(
            value is null
                ? null!
                : ImplementationPlanV3ToAlpha3Migration.ToLegacyShape(value),
            versionTwoValidator,
            AlphaDispositionVersion,
            "0.1.0-alpha.3").Diagnostics);
        if (value?.Design is not null &&
            (!string.Equals(
                value.Design.Identity.Kind,
                "design",
                StringComparison.Ordinal) ||
             value.Design.Version != AlphaDesignVersion))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln143,
                "Planning 0.1.0-alpha.3 requires an exact design artifact at version 0.1.0-alpha.2.",
                "$.design"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
