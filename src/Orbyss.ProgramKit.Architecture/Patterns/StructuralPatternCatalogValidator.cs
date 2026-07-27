using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Patterns;

/// <summary>Validates structural guidance without treating it as doctrine.</summary>
public sealed class StructuralPatternCatalogValidator :
    IProgramKitSemanticValidator<StructuralPatternCatalog>,
    IProgramKitSemanticValidator<ArtifactEnvelope<StructuralPatternCatalog>>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;

    /// <summary>Initializes the validator with shared envelope validation behavior.</summary>
    public StructuralPatternCatalogValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(StructuralPatternCatalog value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc400, "/", "A structural-pattern catalog is required.");
            return diagnostics.ToResult();
        }

        diagnostics.Identifier(value.Identity, "/identity");
        if (!string.Equals(value.Identity.Kind, "catalog", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc401,
                "/identity",
                "A structural-pattern catalog identity must use the 'catalog' PKID kind.");
        }

        diagnostics.Version(value.Version, "/version");
        diagnostics.Required(value.Purpose, "/purpose", "Catalog purpose");

        var patterns = ArchitectureValidation.OrEmpty(value.Patterns);
        if (patterns.Length == 0)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc402, "/patterns", "A catalog must contain at least one pattern.");
        }

        diagnostics.DuplicateIdentifiers(patterns, static pattern => pattern.Identity, "/patterns");
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        for (var index = 0; index < patterns.Length; index++)
        {
            var pattern = patterns[index];
            var path = $"/patterns/{index}";
            diagnostics.Identifier(pattern.Identity, $"{path}/identity");
            diagnostics.Required(pattern.Name, $"{path}/name", "Pattern name");
            diagnostics.Required(pattern.Problem, $"{path}/problem", "Pattern problem");
            if (!string.IsNullOrWhiteSpace(pattern.Name) && !names.Add(pattern.Name))
            {
                diagnostics.Error(ArchitectureDiagnosticIds.Pkarc403, $"{path}/name", "Pattern names must be unique.");
            }

            RequireStatements(
                pattern.ApplicabilityCriteria,
                $"{path}/applicabilityCriteria",
                "applicability criterion",
                diagnostics);
            RequireStatements(pattern.TradeOffs, $"{path}/tradeOffs", "trade-off", diagnostics);
            RequireStatements(
                pattern.MechanicalChecks,
                $"{path}/mechanicalChecks",
                "mechanical check",
                diagnostics);
            RequireStatements(pattern.HumanChecks, $"{path}/humanChecks", "human check", diagnostics);

            var examples = ArchitectureValidation.OrEmpty(pattern.Examples);
            if (examples.Length == 0)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc404,
                    $"{path}/examples",
                    "A structural pattern requires at least one bounded example.");
            }

            for (var exampleIndex = 0; exampleIndex < examples.Length; exampleIndex++)
            {
                var example = examples[exampleIndex];
                var examplePath = $"{path}/examples/{exampleIndex}";
                diagnostics.Required(example.Name, $"{examplePath}/name", "Example name");
                diagnostics.Required(example.Context, $"{examplePath}/context", "Example context");
                diagnostics.Required(
                    example.Application,
                    $"{examplePath}/application",
                    "Example application");
                diagnostics.Required(
                    example.Consequence,
                    $"{examplePath}/consequence",
                    "Example consequence");
            }
        }

        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates an enveloped catalog and requires its self-description to
    /// equal the authoritative envelope identity and version.
    /// </summary>
    public ProgramKitValidationResult Validate(ArtifactEnvelope<StructuralPatternCatalog> value)
    {
        var envelopeResult = envelopeValidator.Validate(value, this);
        if (value?.Document is null || value.Artifact is null)
        {
            return envelopeResult;
        }

        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value.Document.Identity != value.Artifact.Id)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc406,
                "/document/identity",
                "Catalog identity must equal the enclosing artifact identity.");
        }

        if (value.Document.Version != value.Artifact.Version)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc407,
                "/document/version",
                "Catalog version must equal the enclosing artifact version.");
        }

        return ProgramKitValidationResult.Combine(envelopeResult, diagnostics.ToResult());
    }

    private static void RequireStatements(
        System.Collections.Immutable.ImmutableArray<string> statements,
        string path,
        string description,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var values = ArchitectureValidation.OrEmpty(statements);
        if (values.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc405,
                path,
                $"At least one {description} is required.");
        }

        for (var index = 0; index < values.Length; index++)
        {
            diagnostics.Required(values[index], $"{path}/{index}", description);
        }
    }
}
