namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Validates the exact current static-conformance disposition writer.</summary>
public sealed class StaticConformanceDispositionAlpha2Validator :
    IProgramKitSemanticValidator<StaticConformanceDispositionAlpha2>
{
    private static readonly SemanticVersion DesignVersion =
        new("0.1.0-alpha.3");
    private readonly IProgramKitSemanticValidator<StaticConformanceDisposition>
        sharedValidator;

    /// <summary>Initializes validation over the existing decision semantics.</summary>
    public StaticConformanceDispositionAlpha2Validator(
        IProgramKitSemanticValidator<StaticConformanceDisposition> sharedValidator)
    {
        this.sharedValidator = sharedValidator ??
            throw new ArgumentNullException(nameof(sharedValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(StaticConformanceDispositionAlpha2 value)
    {
        var diagnostics =
            System.Collections.Immutable.ImmutableArray
                .CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.Add(sharedValidator.Validate(
            value is null
                ? null!
                : StaticConformanceDispositionV1ToAlpha1Migration.ToLegacyShape(
                    StaticConformanceDispositionAlpha1ToAlpha2Migration
                        .ToAlpha1Shape(value))));
        if (value is null)
        {
            return diagnostics.ToResult();
        }

        if (!string.Equals(
                value.Schema,
                StaticConformanceDispositionAlpha2.SchemaUri,
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc001,
                "/$schema",
                "StaticConformanceDisposition 0.1.0-alpha.2 requires its exact canonical $schema URI.");
        }

        if (!string.Equals(
                value.SoftwareDesign.Identity.Kind,
                "design",
                StringComparison.Ordinal) ||
            value.SoftwareDesign.Version != DesignVersion)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc711,
                "/softwareDesign",
                "StaticConformanceDisposition 0.1.0-alpha.2 requires an exact design artifact at version 0.1.0-alpha.3.");
        }

        return diagnostics.ToResult();
    }
}
