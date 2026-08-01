using System;
using System.IO;
using System.Text.RegularExpressions;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static partial class DisclosureFilter
{
    public static string SafeLogicalValue(string value)
    {
        if (Path.IsPathRooted(value)
            || value.Contains("..", StringComparison.Ordinal)
            || AbsolutePath().IsMatch(value))
        {
            return "withheld";
        }

        return SafeText(value);
    }

    public static string SafeText(string value)
    {
        string singleLine = value.Replace("\r", " ", StringComparison.Ordinal).Replace("\n", " ", StringComparison.Ordinal);
        if (singleLine.Length > 500)
        {
            singleLine = singleLine[..500];
        }

        string[] sensitiveMarkers =
        {
            "password", "passwd", "secret", "token=", "token:", "bearer ", "apikey", "api-key",
            "connectionstring", "private key", "authorization:", "stack trace", "stdout:", "stderr:",
        };
        foreach (string marker in sensitiveMarkers)
        {
            if (singleLine.Contains(marker, StringComparison.OrdinalIgnoreCase))
            {
                return "withheld";
            }
        }

        if (AbsolutePath().IsMatch(singleLine)
            || ExceptionDetail().IsMatch(singleLine))
        {
            return "withheld";
        }

        return singleLine;
    }

    [GeneratedRegex(@"(?i)(?:[a-z]:[\\/]|\\\\[^\\\s]+[\\/]|/(?:home|users|tmp|var|etc|opt)/)", RegexOptions.CultureInvariant)]
    private static partial Regex AbsolutePath();

    [GeneratedRegex(@"(?i)(?:\b[a-z0-9_.]+exception\b|\bat\s+[a-z0-9_.]+\([^)]*:[0-9]+\))", RegexOptions.CultureInvariant)]
    private static partial Regex ExceptionDetail();
}
