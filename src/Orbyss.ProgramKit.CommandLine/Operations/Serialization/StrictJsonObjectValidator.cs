using System.Text.Json;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Rejects malformed JSON and duplicate object properties without a DOM.</summary>
internal static class StrictJsonObjectValidator
{
    /// <summary>Validates one complete strict JSON value.</summary>
    public static void Validate(ReadOnlySpan<byte> content)
    {
        Utf8JsonReader reader = new(
            content,
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
            });
        if (!reader.Read())
        {
            throw new JsonException("A JSON value is required.");
        }

        ValidateValue(ref reader);
        if (reader.Read())
        {
            throw new JsonException(
                "Only one top-level JSON value is permitted.");
        }
    }

    private static void ValidateValue(ref Utf8JsonReader reader)
    {
        if (reader.TokenType == JsonTokenType.StartObject)
        {
            HashSet<string> names = new(StringComparer.Ordinal);
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndObject)
            {
                if (reader.TokenType != JsonTokenType.PropertyName)
                {
                    throw new JsonException(
                        "A JSON object property name was expected.");
                }

                var name = reader.GetString() ??
                    throw new JsonException(
                        "A JSON object property name cannot be null.");
                if (!names.Add(name))
                {
                    throw new JsonException(
                        string.Concat(
                            "JSON property '",
                            name,
                            "' occurs more than once."));
                }

                if (!reader.Read())
                {
                    throw new JsonException(
                        "A JSON object property value was expected.");
                }

                ValidateValue(ref reader);
            }

            return;
        }

        if (reader.TokenType == JsonTokenType.StartArray)
        {
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndArray)
            {
                ValidateValue(ref reader);
            }
        }
    }
}
