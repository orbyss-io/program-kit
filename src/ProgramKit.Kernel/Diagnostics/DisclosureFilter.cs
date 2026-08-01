using System;
using System.IO;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static partial class DisclosureFilter
{
    private static readonly GovernedIdentity DisclosurePolicy = ProtocolIdentities.Rule("diagnostic-disclosure-floor");

    public static string SafeLogicalValue(string value) => Classify(value, logicalPath: true).Value ?? "withheld";

    public static string SafeText(string value) => Classify(value).Value ?? "withheld";

    public static SafeValue Classify(string value, bool logicalPath = false)
    {
        if (MustWithhold(value, logicalPath))
        {
            return Withheld("disclosure-floor");
        }

        string singleLine = value.Replace("\r", " ", StringComparison.Ordinal).Replace("\n", " ", StringComparison.Ordinal);
        if (singleLine.Length > 500)
        {
            singleLine = singleLine[..500];
        }

        return new SafeValue(
            logicalPath ? SafeValueClassification.RepositoryRelative : SafeValueClassification.Public,
            logicalPath ? SafeValueKind.LogicalPath : SafeValueKind.Text,
            singleLine);
    }

    public static SafeValue Withheld(string reason) => new(
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
