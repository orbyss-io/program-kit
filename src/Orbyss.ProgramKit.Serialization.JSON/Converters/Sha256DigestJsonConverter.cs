using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Converters;

internal sealed class Sha256DigestJsonConverter : JsonConverter<Sha256Digest>
{
    public override Sha256Digest Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var value = reader.TokenType == JsonTokenType.String
            ? reader.GetString()
                ?? throw new JsonException("A SHA-256 digest cannot be null.")
            : throw new JsonException("A SHA-256 digest must be a JSON string.");
        try
        {
            return new Sha256Digest(value);
        }
        catch (ArgumentException exception)
        {
            throw new JsonException(
                "A SHA-256 digest has invalid canonical syntax.",
                exception);
        }
    }

    public override void Write(
        Utf8JsonWriter writer,
        Sha256Digest value,
        JsonSerializerOptions options)
    {
        if (value.Value is null)
        {
            throw new JsonException("A SHA-256 digest cannot be the default value.");
        }

        writer.WriteStringValue(value.Value);
    }
}
