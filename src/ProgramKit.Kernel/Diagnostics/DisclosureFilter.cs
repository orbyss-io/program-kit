using System;
using System.IO;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static partial class DisclosureFilter
{
    private static readonly GovernedIdentity DisclosurePolicy = ProtocolIdentities.Rule("diagnostic-disclosure-floor");

    public static SafeValue PublicText(string value) => Visible(
        value,
        SafeValueClassification.Public,
        SafeValueKind.Text,
        logicalPath: false);

    public static SafeValue RepositoryRelative(string value) => Visible(
        value,
        SafeValueClassification.RepositoryRelative,
        SafeValueKind.LogicalPath,
        logicalPath: true);

    public static SafeValue Withhold(string value, string reason)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (string.IsNullOrWhiteSpace(reason))
        {
            throw new ArgumentException("A withheld diagnostic value requires a stable reason.", nameof(reason));
        }

        return Withheld(reason);
    }

    public static SafeValue Enforce(SafeValue value)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (value.Classification == SafeValueClassification.Withheld)
        {
            return value;
        }

        return Visible(
            value.Value ?? throw new ArgumentException("A visible diagnostic value requires content.", nameof(value)),
            value.Classification,
            value.ValueKind,
            value.Classification == SafeValueClassification.RepositoryRelative);
    }

    private static SafeValue Visible(
        string value,
        SafeValueClassification classification,
        SafeValueKind kind,
        bool logicalPath)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (MustWithhold(value, logicalPath))
        {
            return Withheld("disclosure-floor");
        }

        string singleLine = value.Replace("\r", " ", StringComparison.Ordinal).Replace("\n", " ", StringComparison.Ordinal);
        if (singleLine.Length > 500)
        {
            singleLine = singleLine[..500];
        }

        return new SafeValue(classification, kind, singleLine);
    }

    private static SafeValue Withheld(string reason) => new(
        SafeValueClassification.Withheld,
        SafeValueKind.Redacted,
        null,
        reason,
        DisclosurePolicy);

    private static bool MustWithhold(string value, bool logicalPath)
    {
        string singleLine = value.Replace("\r", " ", StringComparison.Ordinal).Replace("\n", " ", StringComparison.Ordinal);
        if (logicalPath && (Path.IsPathRooted(value) || value.Contains("..", StringComparison.Ordinal)))
        {
            return true;
        }

        string[] sensitiveMarkers =
        {
            "password", "passwd", "secret", "token=", "token:", "bearer ", "apikey", "api-key",
            "connectionstring", "private key", "authorization:", "stack trace", "stdout:", "stderr:",
            "rm -rf", "remove-item", "del /", "format ", "cmd /c", "bash -c", "sh -c", "encodedcommand",
        };
        foreach (string marker in sensitiveMarkers)
        {
            if (singleLine.Contains(marker, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return AbsolutePath().IsMatch(singleLine) || ExceptionDetail().IsMatch(singleLine);
    }

    [GeneratedRegex(@"(?i)(?:[a-z]:[\\/]|\\\\[^\\\s]+[\\/]|/(?:home|users|tmp|var|etc|opt)/)", RegexOptions.CultureInvariant)]
    private static partial Regex AbsolutePath();

    [GeneratedRegex(@"(?i)(?:\b[a-z0-9_.]+exception\b|\bat\s+[a-z0-9_.]+\([^)]*:[0-9]+\))", RegexOptions.CultureInvariant)]
    private static partial Regex ExceptionDetail();
}
