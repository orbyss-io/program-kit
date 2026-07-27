using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>Strict parser for the repository-owned capability index table.</summary>
public sealed class CapabilityIndexParser : ICapabilityIndexParser
{
    private const string Header =
        "| Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |";
    private const string Separator =
        "| --- | --- | --- | --- | --- | --- |";
    private static readonly UTF8Encoding StrictUtf8 = new(
        encoderShouldEmitUTF8Identifier: false,
        throwOnInvalidBytes: true);

    /// <inheritdoc />
    public CapabilityIndexDocument Parse(ReadOnlySpan<byte> content)
    {
        string text;
        try
        {
            text = StrictUtf8.GetString(content);
        }
        catch (DecoderFallbackException exception)
        {
            throw InvalidIndex(
                "The capability index must contain valid UTF-8.",
                "/index",
                exception);
        }

        var lines = text
            .Replace("\r\n", "\n", StringComparison.Ordinal)
            .Replace('\r', '\n')
            .Split('\n');
        var headerIndex = Array.FindIndex(
            lines,
            line => string.Equals(line.Trim(), Header, StringComparison.Ordinal));
        if (headerIndex < 0 ||
            headerIndex + 1 >= lines.Length ||
            !string.Equals(
                lines[headerIndex + 1].Trim(),
                Separator,
                StringComparison.Ordinal))
        {
            throw InvalidIndex(
                "The capability index does not contain the exact canonical availability table.",
                "/index/table");
        }

        var entries = ImmutableArray.CreateBuilder<CapabilityIndexEntry>();
        var identifiers = new HashSet<string>(StringComparer.Ordinal);
        for (var lineIndex = headerIndex + 2;
             lineIndex < lines.Length;
             lineIndex++)
        {
            var line = lines[lineIndex].Trim();
            if (line.Length == 0)
            {
                break;
            }

            if (!line.StartsWith('|') || !line.EndsWith('|'))
            {
                throw InvalidIndex(
                    "Every capability index row must use the exact Markdown table shape.",
                    $"/index/lines/{lineIndex + 1}");
            }

            var cells = line[1..^1]
                .Split('|')
                .Select(cell => cell.Trim())
                .ToArray();
            if (cells.Length != 6)
            {
                throw InvalidIndex(
                    "Every capability index row must contain exactly six cells.",
                    $"/index/lines/{lineIndex + 1}");
            }

            var capabilityId = ParseCode(cells[0], lineIndex, "capabilityId");
            ValidateCapabilityId(capabilityId, lineIndex);
            if (!identifiers.Add(capabilityId))
            {
                throw InvalidIndex(
                    $"Capability '{capabilityId}' occurs more than once.",
                    $"/index/lines/{lineIndex + 1}/capabilityId");
            }

            var status = cells[2];
            if (status is not "available" and not "unavailable")
            {
                throw InvalidIndex(
                    "Capability status must be exactly 'available' or 'unavailable'.",
                    $"/index/lines/{lineIndex + 1}/status");
            }

            var canonical = ParseTarget(
                cells[3],
                "Not created",
                lineIndex,
                "canonicalDefinition");
            var wrapper = ParseTarget(
                cells[4],
                "Not registered",
                lineIndex,
                "activeProviderWrapper");
            if (status == "available" &&
                (canonical is null || wrapper is null))
            {
                throw InvalidIndex(
                    "An available capability requires both a canonical definition and active-provider wrapper.",
                    $"/index/lines/{lineIndex + 1}");
            }

            if (status == "unavailable" &&
                (canonical is not null || wrapper is not null))
            {
                throw InvalidIndex(
                    "An unavailable capability cannot point to registered files.",
                    $"/index/lines/{lineIndex + 1}");
            }

            if (cells[1].Length == 0 || cells[5].Length == 0)
            {
                throw InvalidIndex(
                    "Capability category and notes cannot be empty.",
                    $"/index/lines/{lineIndex + 1}");
            }

            entries.Add(
                new CapabilityIndexEntry(
                    capabilityId,
                    cells[1],
                    status,
                    canonical,
                    wrapper,
                    cells[5]));
        }

        if (entries.Count == 0)
        {
            throw InvalidIndex(
                "The capability index table cannot be empty.",
                "/index/table");
        }

        return new CapabilityIndexDocument(entries.ToImmutable());
    }

    private static string ParseCode(
        string value,
        int lineIndex,
        string field)
    {
        if (value.Length < 3 ||
            value[0] != '`' ||
            value[^1] != '`' ||
            value[1..^1].Contains('`', StringComparison.Ordinal))
        {
            throw InvalidIndex(
                "Capability identifiers must use one exact Markdown code span.",
                $"/index/lines/{lineIndex + 1}/{field}");
        }

        return value[1..^1];
    }

    private static string? ParseTarget(
        string value,
        string unavailableText,
        int lineIndex,
        string field)
    {
        if (string.Equals(value, unavailableText, StringComparison.Ordinal))
        {
            return null;
        }

        var openTarget = value.IndexOf("](", StringComparison.Ordinal);
        if (!value.StartsWith('[') ||
            openTarget <= 1 ||
            !value.EndsWith(')') ||
            value.AsSpan(openTarget + 2, value.Length - openTarget - 3)
                .IndexOfAny('(', ')') >= 0)
        {
            throw InvalidIndex(
                "Registered capability files must use one exact Markdown link.",
                $"/index/lines/{lineIndex + 1}/{field}");
        }

        var target = value[(openTarget + 2)..^1];
        if (target.Length == 0 ||
            target.Contains('\\') ||
            Path.IsPathRooted(target))
        {
            throw InvalidIndex(
                "Capability links must use non-empty repository-relative forward-slash paths.",
                $"/index/lines/{lineIndex + 1}/{field}");
        }

        return target;
    }

    private static void ValidateCapabilityId(
        string capabilityId,
        int lineIndex)
    {
        if (capabilityId.Length == 0 ||
            capabilityId[0] == '-' ||
            capabilityId[^1] == '-' ||
            capabilityId.Any(
                character =>
                    character is not (>= 'a' and <= 'z') &&
                    character is not (>= '0' and <= '9') &&
                    character != '-'))
        {
            throw InvalidIndex(
                "Capability identifiers must be lowercase hyphenated values.",
                $"/index/lines/{lineIndex + 1}/capabilityId");
        }
    }

    private static CapabilityOperationException InvalidIndex(
        string message,
        string path,
        Exception? innerException = null)
    {
        var exception = new CapabilityOperationException(
            CommandExitCode.UsageOrInputFailure,
            CommandDiagnosticIds.InvalidCapabilityIndex,
            path,
            message);
        if (innerException is not null)
        {
            exception.Data[nameof(innerException)] =
                innerException.GetType().FullName;
        }

        return exception;
    }
}
