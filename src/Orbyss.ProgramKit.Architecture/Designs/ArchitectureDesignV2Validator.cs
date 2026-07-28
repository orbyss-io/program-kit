using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Validates Architecture Design 2.0 semantics while preserving the independent
/// v1 validator for readable legacy documents.
/// </summary>
public sealed class ArchitectureDesignV2Validator :
    IProgramKitSemanticValidator<ArchitectureDesignDocumentV2>
{
    private static readonly SemanticVersion LegacyDispositionVersion =
        new("1.0.0");
    private readonly IProgramKitSemanticValidator<ArchitectureDesignDocument>
        versionOneValidator;

    /// <summary>Initializes the v2 validator over the existing v1 semantics.</summary>
    public ArchitectureDesignV2Validator(
        IProgramKitSemanticValidator<ArchitectureDesignDocument> versionOneValidator)
    {
        this.versionOneValidator = versionOneValidator ??
            throw new ArgumentNullException(nameof(versionOneValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArchitectureDesignDocumentV2 value) =>
        ValidateVersioned(
            value,
            versionOneValidator,
            LegacyDispositionVersion,
            "2.0");

    internal static ProgramKitValidationResult ValidateVersioned(
        ArchitectureDesignDocumentV2 value,
        IProgramKitSemanticValidator<ArchitectureDesignDocument>
            versionOneValidator,
        SemanticVersion dispositionVersion,
        string designVersion)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc600,
                "/",
                string.Concat(
                    "An Architecture Design ",
                    designVersion,
                    " document is required."));
            return diagnostics.ToResult();
        }

        diagnostics.Add(versionOneValidator.Validate(ToVersionOne(value)));
        diagnostics.Reference(
            value.StaticConformanceDisposition,
            "/staticConformanceDisposition");
        if (value.StaticConformanceDisposition is not null &&
            (!string.Equals(
                 value.StaticConformanceDisposition.Identity.Kind,
                 "static-conformance-disposition",
                 StringComparison.Ordinal) ||
             value.StaticConformanceDisposition.Version != dispositionVersion))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc711,
                "/staticConformanceDisposition",
                string.Concat(
                    "Architecture Design ",
                    designVersion,
                    " requires an exact static-conformance-disposition artifact at version ",
                    dispositionVersion.Value,
                    "."));
        }

        return diagnostics.ToResult();
    }

    private static ArchitectureDesignDocument ToVersionOne(
        ArchitectureDesignDocumentV2 value) =>
        new(
            value.Title,
            value.Intent,
            value.Scope,
            value.NonGoals,
            value.Assumptions,
            value.UnresolvedDecisions,
            value.SourceTruthAuthorities,
            value.Domains,
            value.Contracts,
            value.SemanticModels,
            value.Operations,
            value.Components,
            value.Projects,
            value.Packages,
            value.ReferenceRules,
            value.Extensions,
            value.Configuration,
            value.FeatureActivations,
            value.ArtifactDecisions,
            value.RepresentationRelationships,
            value.Boundaries,
            value.Scenarios,
            value.StatusClaims);
}
