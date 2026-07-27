using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Converters;

internal sealed class SemanticVersionJsonConverter : JsonConverter<SemanticVersion>
{
    public override SemanticVersion Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var value = reader.TokenType == JsonTokenType.String
            ? reader.GetString()
                ?? throw new JsonException("A semantic version cannot be null.")
            : throw new JsonException("A semantic version must be a JSON string.");
        try
        {
            return new SemanticVersion(value);
        }
        catch (ArgumentException exception)
        {
            throw new JsonException(
                "A semantic version has invalid canonical syntax.",
                exception);
        }
    }

    public override void Write(
        Utf8JsonWriter writer,
        SemanticVersion value,
        JsonSerializerOptions options)
    {
        if (value.Value is null)
        {
            throw new JsonException("A semantic version cannot be the default value.");
        }

        writer.WriteStringValue(value.Value);
    }
}
