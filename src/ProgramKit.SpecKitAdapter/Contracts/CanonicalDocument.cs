using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.SpecKitAdapter.Contracts;

public static class CanonicalDocument
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    public static byte[] Encode(JsonNode node)
    {
        JsonNode ordered = Order(node);
        return JsonSerializer.SerializeToUtf8Bytes(ordered, SerializerOptions);
    }

    public static string Digest(JsonNode node) => "sha256:" + Convert.ToHexString(SHA256.HashData(Encode(node))).ToLowerInvariant();

    public static JsonNode Parse(ReadOnlySpan<byte> bytes) => JsonNode.Parse(bytes)
        ?? throw new JsonException("The document is empty.");

    private static JsonNode Order(JsonNode node)
    {
        if (node is JsonObject source)
        {
            JsonObject result = new();
            List<string> names = new(source.Select(static property => property.Key));
            names.Sort(StringComparer.Ordinal);
            foreach (string name in names)
            {
                result[name] = source[name] is JsonNode child ? Order(child) : null;
            }

            return result;
        }

        if (node is JsonArray array)
        {
            JsonArray result = new();
            foreach (JsonNode? child in array)
            {
                result.Add(child is null ? null : Order(child));
            }

            return result;
        }

        return node.DeepClone();
    }
}
