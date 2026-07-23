using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>Validates exact artifact references.</summary>
public sealed class ArtifactReferenceValidator : IProgramKitSemanticValidator<ArtifactReference>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArtifactReference value) =>
        Validate(value, string.Empty);

    internal static ProgramKitValidationResult Validate(
        ArtifactReference? value,
        string path)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactReference,
                "An exact artifact reference is required.",
                path);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, Path(path, "identity")));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, Path(path, "version")));
        diagnostics.Add(Sha256Digest.Validate(value.Digest.Value, Path(path, "digest")));
        return diagnostics.ToResult();
    }

    internal static string Key(ArtifactReference reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);

    internal static string ExactKey(ArtifactReference reference) =>
        string.Concat(Key(reference), "#", reference.Digest.Value);

    internal static string Path(string parent, string child) =>
        string.IsNullOrEmpty(parent) ? string.Concat("/", child) : string.Concat(parent, "/", child);
}
