namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Validates the exact current Architecture Design alpha writer.</summary>
public sealed class ArchitectureDesignAlpha3Validator :
    IProgramKitSemanticValidator<ArchitectureDesignDocumentAlpha3>
{
    private static readonly SemanticVersion DispositionVersion =
        new("0.1.0-alpha.2");
    private readonly IProgramKitSemanticValidator<ArchitectureDesignDocument>
        versionOneValidator;

    /// <summary>Initializes validation over the existing design semantics.</summary>
    public ArchitectureDesignAlpha3Validator(
        IProgramKitSemanticValidator<ArchitectureDesignDocument> versionOneValidator)
    {
        this.versionOneValidator = versionOneValidator ??
            throw new ArgumentNullException(nameof(versionOneValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArchitectureDesignDocumentAlpha3 value)
    {
        var diagnostics =
            System.Collections.Immutable.ImmutableArray
                .CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            return ArchitectureDesignV2Validator.ValidateVersioned(
                null!,
                versionOneValidator,
                DispositionVersion,
                "0.1.0-alpha.3");
        }

        diagnostics.AddRange(ArchitectureDesignV2Validator.ValidateVersioned(
            ArchitectureDesignV2ToAlpha2Migration.ToLegacyShape(
                ArchitectureDesignAlpha2ToAlpha3Migration.ToAlpha2Shape(value)),
            versionOneValidator,
            DispositionVersion,
            "0.1.0-alpha.3").Diagnostics);
        if (!string.Equals(
                value.Schema,
                ArchitectureDesignDocumentAlpha3.SchemaUri,
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc001,
                "/$schema",
                "Architecture Design 0.1.0-alpha.3 requires its exact canonical $schema URI.");
        }

        return diagnostics.ToResult();
    }
}
