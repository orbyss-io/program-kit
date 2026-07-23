using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Converters;

internal sealed class SemanticVersionRangeJsonConverter :
    JsonConverter<SemanticVersionRange>
{
    public override SemanticVersionRange Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var value = reader.TokenType == JsonTokenType.String
            ? reader.GetString()
                ?? throw new JsonException("A semantic version range cannot be null.")
            : throw new JsonException("A semantic version range must be a JSON string.");
        try
        {
            return new SemanticVersionRange(value);
        }
        catch (ArgumentException exception)
        {
            throw new JsonException(
                "A semantic-version range has invalid canonical syntax.",
                exception);
        }
    }

    public override void Write(
        Utf8JsonWriter writer,
        SemanticVersionRange value,
        JsonSerializerOptions options)
    {
        if (value.Value is null)
        {
            throw new JsonException(
                "A semantic-version range cannot be the default value.");
        }

        writer.WriteStringValue(value.Value);
    }
}
