using Orbyss.ProgramKit.DotNet.Diagnostics;

namespace Orbyss.ProgramKit.DotNet.Inputs;

internal static class DotNetPathPolicy
{
    internal static string NormalizeRelative(string value)
    {
        if (string.IsNullOrWhiteSpace(value) ||
            Path.IsPathRooted(value) ||
            value.Contains('\\', StringComparison.Ordinal))
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidArtifactInput,
                "Artifact input paths must be non-empty forward-slash relative paths.",
                "/inputs/relativePath");
        }

        var segments = value.Split('/', StringSplitOptions.None);
        if (segments.Any(static segment =>
                segment.Length == 0 ||
                segment is "." or ".."))
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidArtifactInput,
                "Artifact input paths must be normalized and may not traverse directories.",
                "/inputs/relativePath");
        }

        return string.Join('/', segments);
    }
}
