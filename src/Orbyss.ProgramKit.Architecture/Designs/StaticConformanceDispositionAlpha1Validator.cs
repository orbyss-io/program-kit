namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Validates StaticConformanceDisposition 0.1.0-alpha.1 without changing the
/// five legacy human-decision states.
/// </summary>
public sealed class StaticConformanceDispositionAlpha1Validator :
    IProgramKitSemanticValidator<StaticConformanceDispositionAlpha1>
{
    private static readonly SemanticVersion AlphaDesignVersion =
        new("0.1.0-alpha.2");
    private readonly IProgramKitSemanticValidator<StaticConformanceDisposition>
        sharedValidator;

    /// <summary>Initializes alpha validation over legacy decision semantics.</summary>
    public StaticConformanceDispositionAlpha1Validator(
        IProgramKitSemanticValidator<StaticConformanceDisposition>
            sharedValidator)
    {
        this.sharedValidator = sharedValidator ??
            throw new ArgumentNullException(nameof(sharedValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        StaticConformanceDispositionAlpha1 value)
    {
        var diagnostics =
            System.Collections.Immutable.ImmutableArray
                .CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.Add(sharedValidator.Validate(
            value is null
                ? null!
                : StaticConformanceDispositionV1ToAlpha1Migration
                    .ToLegacyShape(value)));
        if (value?.SoftwareDesign is not null &&
            (!string.Equals(
                value.SoftwareDesign.Identity.Kind,
                "design",
                StringComparison.Ordinal) ||
             value.SoftwareDesign.Version != AlphaDesignVersion))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc711,
                "/softwareDesign",
                "StaticConformanceDisposition 0.1.0-alpha.1 requires an exact design artifact at version 0.1.0-alpha.2.");
        }

        return diagnostics.ToResult();
    }
}
