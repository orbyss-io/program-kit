using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.Kernel.Canonicalization;

public static class CanonicalJson
{
    public const string Profile = "program-kit.canonical-json/v1";
    private const long MaxSafeInteger = 9_007_199_254_740_991;

    public static JsonNode Parse(ReadOnlySpan<byte> utf8)
    {
        JsonDocumentOptions options = new()
        {
            AllowTrailingCommas = false,
            CommentHandling = JsonCommentHandling.Disallow,
            MaxDepth = 128,
            AllowDuplicateProperties = false,
        };
        using JsonDocument document = JsonDocument.Parse(utf8.ToArray(), options);
        Validate(document.RootElement);
        return JsonNode.Parse(document.RootElement.GetRawText())
            ?? throw new JsonException("The JSON document did not contain a value.");
    }

    public static byte[] Encode(JsonNode node)
    {
        ArrayBufferWriter<byte> buffer = new();
        using (Utf8JsonWriter writer = new(buffer, new JsonWriterOptions
        {
            Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            Indented = false,
            SkipValidation = false,
        }))
        {
            WriteNode(writer, node);
        }

        return buffer.WrittenSpan.ToArray();
    }

    public static string EncodeToString(JsonNode node) => Encoding.UTF8.GetString(Encode(node));

    public static string Digest(JsonNode node) => Digests.Sha256(Encode(node));

    private static void WriteNode(Utf8JsonWriter writer, JsonNode? node)
    {
        if (node is null)
        {
            writer.WriteNullValue();
            return;
        }

        switch (node)
        {
            case JsonObject obj:
                writer.WriteStartObject();
                foreach (KeyValuePair<string, JsonNode?> property in obj.OrderBy(static pair => pair.Key, StringComparer.Ordinal))
                {
                    ValidateString(property.Key);
                    writer.WritePropertyName(property.Key);
                    WriteNode(writer, property.Value);
                }

                writer.WriteEndObject();
                return;

            case JsonArray array:
                writer.WriteStartArray();
                foreach (JsonNode? item in array)
                {
                    WriteNode(writer, item);
                }

                writer.WriteEndArray();
                return;

            case JsonValue value:
                if (value.TryGetValue<string>(out string? text))
                {
                    ValidateString(text);
                    writer.WriteStringValue(text);
                }
                else if (value.TryGetValue<bool>(out bool boolean))
                {
                    writer.WriteBooleanValue(boolean);
                }
                else if (value.TryGetValue<long>(out long integer))
                {
                    ValidateInteger(integer);
                    writer.WriteNumberValue(integer);
                }
                else if (value.TryGetValue<int>(out int int32))
                {
                    writer.WriteNumberValue(int32);
                }
                else if (value.TryGetValue<JsonElement>(out JsonElement element))
                {
                    WriteElement(writer, element);
                }
                else
                {
                    throw new JsonException("Canonical JSON permits only null, Boolean, string, array, object, and safe-range integer values.");
                }

                return;

            default:
                throw new JsonException($"Unsupported JSON node type: {node.GetType().Name}");
        }
    }

    private static void WriteElement(Utf8JsonWriter writer, JsonElement element)
    {
        Validate(element);
        switch (element.ValueKind)
        {
            case JsonValueKind.Null:
                writer.WriteNullValue();
                break;
            case JsonValueKind.True:
            case JsonValueKind.False:
                writer.WriteBooleanValue(element.GetBoolean());
                break;
            case JsonValueKind.String:
                string value = element.GetString() ?? string.Empty;
                ValidateString(value);
                writer.WriteStringValue(value);
                break;
            case JsonValueKind.Number:
                writer.WriteNumberValue(element.GetInt64());
                break;
            case JsonValueKind.Array:
                writer.WriteStartArray();
                foreach (JsonElement item in element.EnumerateArray())
                {
                    WriteElement(writer, item);
                }

                writer.WriteEndArray();
                break;
            case JsonValueKind.Object:
                writer.WriteStartObject();
                foreach (JsonProperty property in element.EnumerateObject().OrderBy(static item => item.Name, StringComparer.Ordinal))
                {
                    writer.WritePropertyName(property.Name);
                    WriteElement(writer, property.Value);
                }

                writer.WriteEndObject();
                break;
            default:
                throw new JsonException("Unsupported canonical JSON token.");
        }
    }

    private static void Validate(JsonElement element)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                HashSet<string> names = new(StringComparer.Ordinal);
                foreach (JsonProperty property in element.EnumerateObject())
                {
                    if (!names.Add(property.Name))
                    {
                        throw new JsonException($"Duplicate property: {property.Name}");
                    }

                    ValidateString(property.Name);
                    Validate(property.Value);
                }

                break;
            case JsonValueKind.Array:
                foreach (JsonElement item in element.EnumerateArray())
                {
                    Validate(item);
                }

                break;
            case JsonValueKind.String:
                ValidateString(element.GetString() ?? string.Empty);
                break;
            case JsonValueKind.Number:
                if (!element.TryGetInt64(out long integer))
                {
                    throw new JsonException("Floating-point and exponent-form numbers are not accepted by the canonical profile.");
                }

                ValidateInteger(integer);
                string raw = element.GetRawText();
                if (raw.Contains('.', StringComparison.Ordinal) || raw.Contains('e', StringComparison.OrdinalIgnoreCase) || raw.StartsWith('+'))
                {
                    throw new JsonException("Only base-10 integer lexical forms are accepted.");
                }

                break;
            case JsonValueKind.Null:
            case JsonValueKind.True:
            case JsonValueKind.False:
                break;
            default:
                throw new JsonException("Unsupported JSON token.");
        }
    }

    private static void ValidateInteger(long value)
    {
        if (value is < -MaxSafeInteger or > MaxSafeInteger)
        {
            throw new JsonException("Integer is outside the canonical safe range.");
        }
    }

    private static void ValidateString(string value)
    {
        for (int index = 0; index < value.Length; index++)
        {
            char current = value[index];
            if (char.IsHighSurrogate(current))
            {
                if (index + 1 >= value.Length || !char.IsLowSurrogate(value[index + 1]))
                {
                    throw new JsonException("Lone UTF-16 high surrogate is not accepted.");
                }

                index++;
            }
            else if (char.IsLowSurrogate(current))
            {
                throw new JsonException("Lone UTF-16 low surrogate is not accepted.");
            }
        }
    }
}
