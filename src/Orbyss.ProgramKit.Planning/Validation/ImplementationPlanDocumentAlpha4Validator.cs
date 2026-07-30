using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>Validates the exact current Implementation Plan alpha writer.</summary>
public sealed class ImplementationPlanDocumentAlpha4Validator :
    IProgramKitSemanticValidator<ImplementationPlanDocumentAlpha4>
{
    private static readonly SemanticVersion DesignVersion =
        new("0.1.0-alpha.3");
    private static readonly SemanticVersion DispositionVersion =
        new("0.1.0-alpha.2");
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocument>
        versionTwoValidator;

    /// <summary>Initializes validation over the existing plan semantics.</summary>
    public ImplementationPlanDocumentAlpha4Validator(
        IProgramKitSemanticValidator<ImplementationPlanDocument> versionTwoValidator)
    {
        this.versionTwoValidator = versionTwoValidator ??
            throw new ArgumentNullException(nameof(versionTwoValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ImplementationPlanDocumentAlpha4 value)
    {
        var diagnostics =
            System.Collections.Immutable.ImmutableArray
                .CreateBuilder<
                    Orbyss.ProgramKit.Artifacts.Diagnostics.ProgramKitDiagnostic>();
        diagnostics.AddRange(ImplementationPlanDocumentV3Validator.ValidateVersioned(
            value is null
                ? null!
                : ImplementationPlanV3ToAlpha3Migration.ToLegacyShape(
                    ImplementationPlanAlpha3ToAlpha4Migration.ToAlpha3Shape(value)),
            versionTwoValidator,
            DispositionVersion,
            "0.1.0-alpha.4").Diagnostics);
        if (value is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (!string.Equals(
                value.Schema,
                ImplementationPlanDocumentAlpha4.SchemaUri,
                StringComparison.Ordinal))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln001,
                "Implementation Plan 0.1.0-alpha.4 requires its exact canonical $schema URI.",
                "/$schema"));
        }

        if (!string.Equals(
                value.Design.Identity.Kind,
                "design",
                StringComparison.Ordinal) ||
            value.Design.Version != DesignVersion)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln143,
                "Planning 0.1.0-alpha.4 requires an exact design artifact at version 0.1.0-alpha.3.",
                "/design"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
