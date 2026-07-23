using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>Validates exact profile references.</summary>
public sealed class ProfileReferenceValidator : IProgramKitSemanticValidator<ProfileReference>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ProfileReference value) =>
        Validate(value, string.Empty);

    internal static ProgramKitValidationResult Validate(
        ProfileReference? value,
        string path)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidProfileReference,
                "An exact profile reference is required.",
                path);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, ArtifactReferenceValidator.Path(path, "identity")));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, ArtifactReferenceValidator.Path(path, "version")));
        diagnostics.Add(Sha256Digest.Validate(value.Digest.Value, ArtifactReferenceValidator.Path(path, "digest")));
        if (!string.Equals(value.Identity.Kind, "profile", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidProfileReference,
                "A profile reference identity must have PKID kind 'profile'.",
                ArtifactReferenceValidator.Path(path, "identity"));
        }

        return diagnostics.ToResult();
    }
}
