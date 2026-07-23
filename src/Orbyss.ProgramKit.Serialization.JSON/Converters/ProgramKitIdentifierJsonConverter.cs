using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Converters;

internal sealed class ProgramKitIdentifierJsonConverter :
    JsonConverter<ProgramKitIdentifier>
{
    public override ProgramKitIdentifier Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var value = reader.TokenType == JsonTokenType.String
            ? reader.GetString()
                ?? throw new JsonException("A Program Kit identifier cannot be null.")
            : throw new JsonException("A Program Kit identifier must be a JSON string.");
        try
        {
            return new ProgramKitIdentifier(value);
        }
        catch (ArgumentException exception)
        {
            throw new JsonException(
                "A Program Kit identifier has invalid canonical syntax.",
                exception);
        }
    }

    public override void Write(
        Utf8JsonWriter writer,
        ProgramKitIdentifier value,
        JsonSerializerOptions options)
    {
        if (value.Value is null)
        {
            throw new JsonException("A Program Kit identifier cannot be the default value.");
        }

        writer.WriteStringValue(value.Value);
    }
}
