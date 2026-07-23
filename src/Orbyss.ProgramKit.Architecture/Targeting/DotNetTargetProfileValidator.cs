using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Targeting;

/// <summary>Validates the one canonical .NET 10 target profile approved by W010.</summary>
public sealed class DotNetTargetProfileValidator :
    IProgramKitSemanticValidator<DotNetTargetProfile>,
    IProgramKitSemanticValidator<ArtifactEnvelope<DotNetTargetProfile>>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;

    /// <summary>Initializes the validator with shared envelope validation behavior.</summary>
    public DotNetTargetProfileValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DotNetTargetProfile value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc500, "/", "A .NET target profile is required.");
            return diagnostics.ToResult();
        }

        diagnostics.Identifier(value.Identity, "/identity");
        diagnostics.Version(value.Version, "/version");
        diagnostics.Required(value.SdkVersion, "/sdkVersion", ".NET SDK version");
        diagnostics.Required(value.RollForward, "/rollForward", "SDK roll-forward policy");
        diagnostics.Required(value.TargetFramework, "/targetFramework", "Target framework");
        diagnostics.Required(value.LanguageVersion, "/languageVersion", "C# language version");

        var canonical = DotNetTargetProfile.ProgramKitDotNet10;
        RequireExact(
            value.Identity.Value,
            canonical.Identity.Value,
            "/identity",
            "target-profile identity",
            diagnostics);
        RequireExact(
            value.Version.Value,
            canonical.Version.Value,
            "/version",
            "target-profile version",
            diagnostics);
        RequireExact(value.SdkVersion, canonical.SdkVersion, "/sdkVersion", "SDK version", diagnostics);
        RequireExact(
            value.RollForward,
            canonical.RollForward,
            "/rollForward",
            "roll-forward policy",
            diagnostics);
        if (value.AllowPrerelease)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc501,
                "/allowPrerelease",
                "The canonical profile forbids prerelease SDK selection.");
        }

        RequireExact(
            value.TargetFramework,
            canonical.TargetFramework,
            "/targetFramework",
            "target framework",
            diagnostics);
        RequireExact(
            value.LanguageVersion,
            canonical.LanguageVersion,
            "/languageVersion",
            "language version",
            diagnostics);

        if (value.TargetFramework?.Contains(';', StringComparison.Ordinal) == true ||
            value.TargetFramework?.Contains(',', StringComparison.Ordinal) == true)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc502,
                "/targetFramework",
                "A target profile selects exactly one target framework; multitargeting is forbidden.");
        }

        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates an enveloped target profile and requires its self-description
    /// to equal the authoritative envelope identity and version.
    /// </summary>
    public ProgramKitValidationResult Validate(ArtifactEnvelope<DotNetTargetProfile> value)
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
                ArchitectureDiagnosticIds.Pkarc504,
                "/document/identity",
                "Target-profile identity must equal the enclosing artifact identity.");
        }

        if (value.Document.Version != value.Artifact.Version)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc505,
                "/document/version",
                "Target-profile version must equal the enclosing artifact version.");
        }

        return ProgramKitValidationResult.Combine(envelopeResult, diagnostics.ToResult());
    }

    private static void RequireExact(
        string? actual,
        string expected,
        string path,
        string description,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!string.Equals(actual, expected, StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc503,
                path,
                $"The canonical Program Kit {description} is '{expected}'.");
        }
    }
}
