using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Compatibility;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

internal sealed class CompatibilityClaimJsonConverter :
    JsonConverter<CompatibilityClaim>
{
    public override CompatibilityClaim Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("A compatibility claim must be an object.");
        }

        CompatibilityDimension dimension = default;
        CompatibilityClassification classification = default;
        ImmutableArray<string> conditions = default;
        var properties = 0;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException("A compatibility claim property name is required.");
            }

            var property = reader.GetString();
            reader.Read();
            switch (property)
            {
                case "dimension":
                    dimension = JsonSerializer.Deserialize<CompatibilityDimension>(
                        ref reader,
                        options);
                    properties++;
                    break;
                case "classification":
                    classification =
                        JsonSerializer.Deserialize<CompatibilityClassification>(
                            ref reader,
                            options);
                    properties++;
                    break;
                case "conditions":
                    conditions = JsonSerializer.Deserialize<ImmutableArray<string>>(
                        ref reader,
                        options);
                    properties++;
                    break;
                default:
                    throw new JsonException(
                        string.Concat(
                            "Unknown compatibility claim property: ",
                            property));
            }
        }

        if (properties != 3 || conditions.IsDefault)
        {
            throw new JsonException(
                "A compatibility claim requires dimension, classification, and conditions.");
        }

        return new CompatibilityClaim(dimension, classification, conditions);
    }

    public override void Write(
        Utf8JsonWriter writer,
        CompatibilityClaim value,
        JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WritePropertyName("dimension");
        JsonSerializer.Serialize(writer, value.Dimension, options);
        writer.WritePropertyName("classification");
        JsonSerializer.Serialize(writer, value.Classification, options);
        writer.WritePropertyName("conditions");
        JsonSerializer.Serialize(writer, value.Conditions, options);
        writer.WriteEndObject();
    }
}
