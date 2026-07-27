using System.Diagnostics.CodeAnalysis;

namespace Orbyss.ProgramKit.Artifacts.Primitives;

internal static class SemanticVersionParser
{
    public static bool TryParse(
        [NotNullWhen(true)] string? value,
        out ParsedSemanticVersion version)
    {
        version = default;
        if (string.IsNullOrEmpty(value) || value.Any(char.IsWhiteSpace))
        {
            return false;
        }

        var plusIndex = value.IndexOf('+');
        var versionWithoutBuild = plusIndex >= 0 ? value[..plusIndex] : value;
        var build = plusIndex >= 0 ? value[(plusIndex + 1)..] : null;
        if (plusIndex >= 0 &&
            (string.IsNullOrEmpty(build) ||
             value.IndexOf('+', plusIndex + 1) >= 0 ||
             !IdentifiersAreValid(build, allowLeadingZero: true)))
        {
            return false;
        }

        var dashIndex = versionWithoutBuild.IndexOf('-');
        var core = dashIndex >= 0 ? versionWithoutBuild[..dashIndex] : versionWithoutBuild;
        var prereleaseText = dashIndex >= 0 ? versionWithoutBuild[(dashIndex + 1)..] : null;
        if (dashIndex >= 0 &&
            (string.IsNullOrEmpty(prereleaseText) ||
             !IdentifiersAreValid(prereleaseText, allowLeadingZero: false)))
        {
            return false;
        }

        var coreParts = core.Split('.');
        if (coreParts.Length != 3 ||
            !TryParseCoreNumber(coreParts[0], out var major) ||
            !TryParseCoreNumber(coreParts[1], out var minor) ||
            !TryParseCoreNumber(coreParts[2], out var patch))
        {
            return false;
        }

        version = new ParsedSemanticVersion(
            major,
            minor,
            patch,
            prereleaseText?.Split('.') ?? []);
        return true;
    }

    private static bool TryParseCoreNumber(string text, out string value)
    {
        value = text;
        return text.Length > 0 &&
               (text.Length == 1 || text[0] != '0') &&
               text.All(static character => character is >= '0' and <= '9');
    }

    private static bool IdentifiersAreValid(string value, bool allowLeadingZero)
    {
        foreach (var identifier in value.Split('.'))
        {
            if (identifier.Length == 0 ||
                identifier.Any(static character =>
                    character is not (>= '0' and <= '9') and
                    not (>= 'A' and <= 'Z') and
                    not (>= 'a' and <= 'z') and
                    not '-'))
            {
                return false;
            }

            var numeric = identifier.All(static character => character is >= '0' and <= '9');
            if (!allowLeadingZero && numeric && identifier.Length > 1 && identifier[0] == '0')
            {
                return false;
            }
        }

        return true;
    }
}
