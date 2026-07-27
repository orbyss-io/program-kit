using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

/// <summary>Exact UTC round-trip converter for material-free secret lifecycle timestamps.</summary>
internal sealed class SecretLifecycleDateTimeOffsetJsonConverter :
    JsonConverter<DateTimeOffset>
{
    /// <inheritdoc />
    public override DateTimeOffset Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        _ = typeToConvert;
        _ = options;
        var value = reader.GetString();
        if (!DateTimeOffset.TryParseExact(
                value,
                "O",
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var parsed))
        {
            throw new JsonException(
                "Secret lifecycle timestamps must use the exact round-trip ISO 8601 format.");
        }

        return parsed.ToUniversalTime();
    }

    /// <inheritdoc />
    public override void Write(
        Utf8JsonWriter writer,
        DateTimeOffset value,
        JsonSerializerOptions options)
    {
        _ = options;
        writer.WriteStringValue(
            value.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture));
    }
}
