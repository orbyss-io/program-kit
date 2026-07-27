using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization.Converters;

internal sealed class CommandRoundTripDateTimeOffsetJsonConverter :
    JsonConverter<DateTimeOffset>
{
    public override DateTimeOffset Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var value = reader.GetString();
        return value is not null &&
            DateTimeOffset.TryParseExact(
                value,
                "O",
                CultureInfo.InvariantCulture,
                DateTimeStyles.None,
                out var result)
            ? result
            : throw new JsonException(
                "DateTimeOffset values require the exact round-trip format.");
    }

    public override void Write(
        Utf8JsonWriter writer,
        DateTimeOffset value,
        JsonSerializerOptions options) =>
        writer.WriteStringValue(value.ToString("O", CultureInfo.InvariantCulture));
}
