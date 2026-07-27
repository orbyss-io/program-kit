using System.Text.Json;
using System.Text.Json.Serialization;
using ObservatoryScheduling.Core.Contracts.Time;

namespace ObservatoryScheduling.Core.Configuration;

/// <summary>Model-first converter for the fixture-owned observatory window contract.</summary>
public sealed class ObservatoryWindowJsonConverter : JsonConverter<ObservatoryWindow>
{
    /// <inheritdoc />
    public override ObservatoryWindow Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("An observatory window must be a JSON object.");
        }

        DateTimeOffset? startsAt = null;
        DateTimeOffset? endsAt = null;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException("An observatory window contains an invalid member.");
            }

            var propertyName = reader.GetString();
            if (!reader.Read() || reader.TokenType != JsonTokenType.String)
            {
                throw new JsonException("Observatory window timestamps must be strings.");
            }

            switch (propertyName)
            {
                case "startsAt" when startsAt is null:
                    startsAt = reader.GetDateTimeOffset();
                    break;
                case "endsAt" when endsAt is null:
                    endsAt = reader.GetDateTimeOffset();
                    break;
                default:
                    throw new JsonException(
                        "An observatory window contains an unknown or duplicate member.");
            }
        }

        if (startsAt is null || endsAt is null || startsAt >= endsAt)
        {
            throw new JsonException(
                "An observatory window requires an ordered start and end.");
        }

        return new ObservatoryWindow(startsAt.Value, endsAt.Value);
    }

    /// <inheritdoc />
    public override void Write(
        Utf8JsonWriter writer,
        ObservatoryWindow value,
        JsonSerializerOptions options)
    {
        ArgumentNullException.ThrowIfNull(writer);
        ArgumentNullException.ThrowIfNull(value);
        if (value.StartsAt >= value.EndsAt)
        {
            throw new JsonException(
                "An observatory window requires an ordered start and end.");
        }

        writer.WriteStartObject();
        writer.WriteString("startsAt", value.StartsAt);
        writer.WriteString("endsAt", value.EndsAt);
        writer.WriteEndObject();
    }
}
