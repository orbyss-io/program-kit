namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Validates Architecture Design 0.1.0-alpha.2 and its exact alpha
/// static-conformance disposition reference.
/// </summary>
public sealed class ArchitectureDesignAlpha2Validator :
    IProgramKitSemanticValidator<ArchitectureDesignDocumentAlpha2>
{
    private static readonly SemanticVersion AlphaDispositionVersion =
        new("0.1.0-alpha.1");
    private readonly IProgramKitSemanticValidator<ArchitectureDesignDocument>
        versionOneValidator;

    /// <summary>Initializes validation over the existing v1 semantics.</summary>
    public ArchitectureDesignAlpha2Validator(
        IProgramKitSemanticValidator<ArchitectureDesignDocument>
            versionOneValidator)
    {
        this.versionOneValidator = versionOneValidator ??
            throw new ArgumentNullException(nameof(versionOneValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        ArchitectureDesignDocumentAlpha2 value) =>
        ArchitectureDesignV2Validator.ValidateVersioned(
            value is null
                ? null!
                : ArchitectureDesignV2ToAlpha2Migration.ToLegacyShape(value),
            versionOneValidator,
            AlphaDispositionVersion,
            "0.1.0-alpha.2");
}
