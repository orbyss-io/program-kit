using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Validates profile-source path and digest integrity rules.</summary>
public sealed class JsonProfileSourceDescriptorValidator :
    IProgramKitSemanticValidator<JsonProfileSourceDescriptor>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(JsonProfileSourceDescriptor value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null || value.OwnedMechanicsSources.IsDefault)
        {
            diagnostics.Add(Error(
                "A profile source and initialized mechanics-source list are required.",
                "/ownedMechanicsSources"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        var paths = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.OwnedMechanicsSources.Length; index++)
        {
            var source = value.OwnedMechanicsSources[index];
            var path = string.Concat("/ownedMechanicsSources/", index);
            if (source is null ||
                !IsNormalizedRelativePath(source.RelativePath))
            {
                diagnostics.Add(Error(
                    "A mechanics source path must be normalized, relative, slash-separated, and contain no dot or dot-dot segments.",
                    string.Concat(path, "/relativePath")));
                continue;
            }

            if (!paths.Add(source.RelativePath))
            {
                diagnostics.Add(Error(
                    $"Mechanics source path '{source.RelativePath}' occurs more than once.",
                    string.Concat(path, "/relativePath")));
            }

            if (!Sha256Digest.Validate(source.Digest.Value).IsValid)
            {
                diagnostics.Add(Error(
                    "A mechanics source requires an exact SHA-256 digest.",
                    string.Concat(path, "/digest")));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static bool IsNormalizedRelativePath(string path)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            Path.IsPathRooted(path) ||
            path.Contains('\\', StringComparison.Ordinal))
        {
            return false;
        }

        var segments = path.Split('/');
        return segments.All(static segment =>
            segment.Length > 0 &&
            segment is not "." and not ".." &&
            segment.All(static character =>
                char.IsAsciiLetterOrDigit(character) ||
                character is '_' or '.' or '-'));
    }

    private static ProgramKitDiagnostic Error(string message, string path) =>
        new(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path);
}
