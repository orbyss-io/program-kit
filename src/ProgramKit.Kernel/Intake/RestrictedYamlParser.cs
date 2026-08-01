using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;

namespace Orbyss.ProgramKit.Kernel.Intake;

public readonly record struct SourcePosition(long Line, long Column, long Offset);

public readonly record struct SourceSpan(SourcePosition Start, SourcePosition End);

public sealed record RestrictedYamlDocument(
    JsonNode Value,
    IReadOnlyDictionary<string, SourceSpan> SourceSpans);

public sealed class RestrictedYamlParser
{
    private const int MaxBytes = 1_048_576;
    private const int MaxDepth = 64;
    private const int MaxNodes = 20_000;
    private const int MaxScalarLength = 65_536;
    private int nodeCount;

    public JsonNode Parse(ReadOnlySpan<byte> utf8) => ParseDocument(utf8).Value;

    public RestrictedYamlDocument ParseDocument(ReadOnlySpan<byte> utf8)
    {
        if (utf8.Length > MaxBytes)
        {
            throw new YamlException("Restricted YAML input exceeds the byte limit.");
        }

        string text = new UTF8Encoding(false, true).GetString(utf8);
        Parser parser = new(new StringReader(text));
        parser.Consume<StreamStart>();
        parser.Consume<DocumentStart>();
        nodeCount = 0;
        Dictionary<string, SourceSpan> spans = new(StringComparer.Ordinal);
        JsonNode result = ParseNode(parser, 0, string.Empty, spans);
        parser.Consume<DocumentEnd>();
        parser.Consume<StreamEnd>();
        return new RestrictedYamlDocument(
            result,
            new ReadOnlyDictionary<string, SourceSpan>(spans));
    }

    private JsonNode ParseNode(
        IParser parser,
        int depth,
        string pointer,
        IDictionary<string, SourceSpan> spans)
    {
        if (depth > MaxDepth || ++nodeCount > MaxNodes)
        {
            throw new YamlException("Restricted YAML input exceeds its depth or node limit.");
        }

        if (parser.Accept<AnchorAlias>(out _))
        {
            throw new YamlException("Aliases are not supported by program-kit.restricted-yaml/v1.");
        }

        if (parser.Accept<MappingStart>(out MappingStart? mappingStart))
        {
            EnsurePlainNode(mappingStart.Anchor.IsEmpty, mappingStart.Tag.IsEmpty);
            MappingStart start = parser.Consume<MappingStart>();
            JsonObject map = new();
            while (!parser.Accept<MappingEnd>(out _))
            {
                Scalar keyEvent = parser.Consume<Scalar>();
                EnsurePlainNode(keyEvent.Anchor.IsEmpty, keyEvent.Tag.IsEmpty);
                string key = keyEvent.Value;
                if (string.IsNullOrEmpty(key) || key.Length > MaxScalarLength || map.ContainsKey(key))
                {
                    throw new YamlException($"Duplicate, empty, or oversized mapping key: {SafeKey(key)}");
                }

                string childPointer = $"{pointer}/{EscapePointer(key)}";
                map.Add(key, ParseNode(parser, depth + 1, childPointer, spans));
            }

            MappingEnd end = parser.Consume<MappingEnd>();
            spans[pointer] = Span(start.Start, end.End);
            return map;
        }

        if (parser.Accept<SequenceStart>(out SequenceStart? sequenceStart))
        {
            EnsurePlainNode(sequenceStart.Anchor.IsEmpty, sequenceStart.Tag.IsEmpty);
            SequenceStart start = parser.Consume<SequenceStart>();
            JsonArray array = new();
            int index = 0;
            while (!parser.Accept<SequenceEnd>(out _))
            {
                array.Add(ParseNode(parser, depth + 1, $"{pointer}/{index}", spans));
                index++;
            }

            SequenceEnd end = parser.Consume<SequenceEnd>();
            spans[pointer] = Span(start.Start, end.End);
            return array;
        }

        Scalar scalar = parser.Consume<Scalar>();
        EnsurePlainNode(scalar.Anchor.IsEmpty, scalar.Tag.IsEmpty);
        if (scalar.Value.Length > MaxScalarLength)
        {
            throw new YamlException("Restricted YAML scalar exceeds the length limit.");
        }

        spans[pointer] = Span(scalar.Start, scalar.End);
        if (scalar.Style is ScalarStyle.SingleQuoted or ScalarStyle.DoubleQuoted or ScalarStyle.Literal or ScalarStyle.Folded)
        {
            return JsonValue.Create(scalar.Value)!;
        }

        if (scalar.Value == "null")
        {
            return null!;
        }

        if (scalar.Value == "true")
        {
            return JsonValue.Create(true)!;
        }

        if (scalar.Value == "false")
        {
            return JsonValue.Create(false)!;
        }

        if (long.TryParse(scalar.Value, NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out long integer))
        {
            if (integer is < -9_007_199_254_740_991 or > 9_007_199_254_740_991)
            {
                throw new YamlException("Integer is outside the canonical safe range.");
            }

            return JsonValue.Create(integer)!;
        }

        if (LooksLikeForbiddenPlainScalar(scalar.Value))
        {
            throw new YamlException("Floating point, alternate-base, implicit-null, and non-finite scalars are not supported.");
        }

        return JsonValue.Create(scalar.Value)!;
    }

    private static SourceSpan Span(Mark start, Mark end) => new(
        new SourcePosition(start.Line + 1, start.Column + 1, start.Index),
        new SourcePosition(end.Line + 1, end.Column + 1, end.Index));

    private static string EscapePointer(string value) => value
        .Replace("~", "~0", StringComparison.Ordinal)
        .Replace("/", "~1", StringComparison.Ordinal);

    private static string SafeKey(string value) => value.Length <= 100 ? value : value[..100];

    private static bool LooksLikeForbiddenPlainScalar(string value)
    {
        bool startsNumeric = value.Length > 0 && (char.IsDigit(value[0]) || value[0] is '+' or '-');
        return value is "~" or ".nan" or ".NaN" or ".NAN" or ".inf" or ".Inf" or ".INF" or "-.inf" or "+.inf"
            || value.StartsWith("0x", StringComparison.OrdinalIgnoreCase)
            || value.StartsWith("0o", StringComparison.OrdinalIgnoreCase)
            || (startsNumeric && (value.Contains('.', StringComparison.Ordinal) || value.Contains('e', StringComparison.OrdinalIgnoreCase)));
    }

    private static void EnsurePlainNode(bool anchorEmpty, bool tagEmpty)
    {
        if (!anchorEmpty || !tagEmpty)
        {
            throw new YamlException("Anchors and explicit tags are not supported by program-kit.restricted-yaml/v1.");
        }
    }
}
