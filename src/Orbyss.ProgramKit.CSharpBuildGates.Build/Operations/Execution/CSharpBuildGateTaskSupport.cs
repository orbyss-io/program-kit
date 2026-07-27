using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Build.Framework;

namespace Orbyss.ProgramKit.CSharpBuildGates.Build.Operations.Execution;

internal static class CSharpBuildGateTaskSupport
{
    internal static readonly string[] Commands =
    [
        "build",
        "test",
        "pack",
        "publish",
        "generated-project-verify",
    ];

    internal static readonly string[] Boundaries =
    [
        "gate-establishment",
        "preflight",
        "work-unit",
        "generated-output",
        "final-closure",
    ];

    internal static readonly string[] VerificationProfiles =
    [
        "bootstrap",
        "focused",
        "work-unit",
        "generated-output",
        "tamper",
        "performance",
        "final-closure",
    ];

    internal static readonly string[] InputKinds =
    [
        "project",
        "physical-source",
        "consumer-generated-source",
        "reference",
        "additional-file",
        "analyzer-config",
    ];

    internal static string CanonicalPath(string path) =>
        Path.GetFullPath(path).TrimEnd(
            Path.DirectorySeparatorChar,
            Path.AltDirectorySeparatorChar);

    internal static bool IsUnder(string child, string parent)
    {
        var canonicalChild = CanonicalPath(child);
        var canonicalParent = CanonicalPath(parent);
        return canonicalChild.StartsWith(
            string.Concat(canonicalParent, Path.DirectorySeparatorChar),
            StringComparison.OrdinalIgnoreCase);
    }

    internal static string FileDigest(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }

    internal static string TextDigest(IEnumerable<string> values)
    {
        var canonical = string.Join(
            "\n",
            values.Order(StringComparer.Ordinal));
        return Convert
            .ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)))
            .ToLowerInvariant();
    }

    internal static bool DigestMatches(string expected, string actual) =>
        string.Equals(
            expected.StartsWith("sha256:", StringComparison.Ordinal)
                ? expected[7..]
                : expected,
            actual,
            StringComparison.OrdinalIgnoreCase);

    internal static string RequiredMetadata(
        ITaskItem item,
        string name)
    {
        var value = item.GetMetadata(name);
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException(
                $"Item '{item.ItemSpec}' requires exact {name} metadata.");
        }

        return value;
    }

    internal static DateTimeOffset ParseTimestamp(string value, string name)
    {
        if (!DateTimeOffset.TryParseExact(
                value,
                "O",
                CultureInfo.InvariantCulture,
                DateTimeStyles.None,
                out var result))
        {
            throw new InvalidOperationException(
                $"{name} must be an exact round-trip timestamp.");
        }

        return result;
    }

    internal static int ParseNonNegativeInt(string value, string name)
    {
        if (!int.TryParse(
                value,
                NumberStyles.None,
                CultureInfo.InvariantCulture,
                out var result) ||
            result < 0)
        {
            throw new InvalidOperationException(
                $"{name} must be a non-negative invariant integer.");
        }

        return result;
    }

    internal static string Substitute(
        string template,
        string nonce,
        string project,
        string profile) =>
        template
            .Replace("{nonce}", nonce, StringComparison.Ordinal)
            .Replace("{project}", project, StringComparison.Ordinal)
            .Replace("{profile}", profile, StringComparison.Ordinal);

    internal static string JsonString(string value) =>
        string.Concat(
            "\"",
            value
                .Replace("\\", "\\\\", StringComparison.Ordinal)
                .Replace("\"", "\\\"", StringComparison.Ordinal)
                .Replace("\r", "\\r", StringComparison.Ordinal)
                .Replace("\n", "\\n", StringComparison.Ordinal),
            "\"");
}
