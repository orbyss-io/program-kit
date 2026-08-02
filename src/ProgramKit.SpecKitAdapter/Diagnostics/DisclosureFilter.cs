using System;
using System.IO;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

public static partial class DisclosureFilter
{
    private static readonly GovernedIdentity Policy = ProtocolIdentities.Rule("adapter-disclosure-floor");

    public static SafeValue PublicText(string value) => Visible(value, SafeValueClassification.Public, SafeValueKind.Text, logicalPath: false);

    public static SafeValue RepositoryPath(string value) => Visible(value, SafeValueClassification.RepositoryRelative, SafeValueKind.LogicalPath, logicalPath: true);

    public static SafeValue External(string reason)
    {
        if (string.IsNullOrWhiteSpace(reason)) throw new ArgumentException("A withheld external value requires a stable reason.", nameof(reason));
        return new SafeValue(SafeValueClassification.Withheld, SafeValueKind.Redacted, null, reason, Policy);
    }

    public static SafeValue Enforce(SafeValue value)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (value.Classification == SafeValueClassification.Withheld) return value;
        return Visible(
            value.Value ?? throw new ArgumentException("A visible diagnostic value requires content.", nameof(value)),
            value.Classification,
            value.ValueKind,
            value.Classification == SafeValueClassification.RepositoryRelative);
    }

    private static SafeValue Visible(string value, SafeValueClassification classification, SafeValueKind kind, bool logicalPath)
    {
        ArgumentNullException.ThrowIfNull(value);
        if ((logicalPath && (Path.IsPathRooted(value) || value.Contains("..", StringComparison.Ordinal) || value.Contains('\\')))
            || Sensitive().IsMatch(value)
            || AbsolutePath().IsMatch(value)
            || ExceptionDetail().IsMatch(value))
            return External("adapter-disclosure-floor");

        string singleLine = WhiteSpace().Replace(value, " ").Trim();
        if (singleLine.Length > 500) singleLine = singleLine[..489] + "[truncated]";
        return new SafeValue(classification, kind, singleLine);
    }

    [GeneratedRegex(@"(?i)(?:password|passwd|secret|token\s*[:=]|bearer\s|api[-_]?key|authorization\s*:|private\s+key|connection\s*string|stdout\s*:|stderr\s*:|stack\s+trace|rm\s+-rf|remove-item|cmd\s+/c|bash\s+-c|sh\s+-c|encodedcommand|raw\s+tool\s+output)", RegexOptions.CultureInvariant)]
    private static partial Regex Sensitive();

    [GeneratedRegex(@"(?i)(?:[a-z]:[\\/]|\\\\[^\\\s]+[\\/]|/(?:home|users|tmp|var|etc|opt)/)", RegexOptions.CultureInvariant)]
    private static partial Regex AbsolutePath();

    [GeneratedRegex(@"(?i)(?:\b[a-z0-9_.]+exception\b|\bat\s+[a-z0-9_.]+\([^)]*:[0-9]+\))", RegexOptions.CultureInvariant)]
    private static partial Regex ExceptionDetail();

    [GeneratedRegex(@"\s+", RegexOptions.CultureInvariant)]
    private static partial Regex WhiteSpace();
}
