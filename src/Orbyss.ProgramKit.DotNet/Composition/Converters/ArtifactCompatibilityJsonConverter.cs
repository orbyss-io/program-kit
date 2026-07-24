using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Compatibility;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

internal sealed class ArtifactCompatibilityJsonConverter :
    JsonConverter<ArtifactCompatibility>
{
    public override ArtifactCompatibility Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("Artifact compatibility must be an object.");
        }

        ProgramKitIdentifier policy = default;
        ImmutableArray<CompatibilityClaim> dimensions = default;
        SemanticVersionRange readerRange = default;
        SemanticVersionRange writerRange = default;
        ImmutableArray<ArtifactReference> migrations = default;
        var properties = 0;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException(
                    "An artifact compatibility property name is required.");
            }

            var property = reader.GetString();
            reader.Read();
            switch (property)
            {
                case "policy":
                    policy = JsonSerializer.Deserialize<ProgramKitIdentifier>(
                        ref reader,
                        options);
                    properties++;
                    break;
                case "dimensions":
                    dimensions =
                        JsonSerializer.Deserialize<ImmutableArray<CompatibilityClaim>>(
                            ref reader,
                            options);
                    properties++;
                    break;
                case "readerRange":
                    readerRange = JsonSerializer.Deserialize<SemanticVersionRange>(
                        ref reader,
                        options);
                    properties++;
                    break;
                case "writerRange":
                    writerRange = JsonSerializer.Deserialize<SemanticVersionRange>(
                        ref reader,
                        options);
                    properties++;
                    break;
                case "migrationReferences":
                    migrations =
                        JsonSerializer.Deserialize<ImmutableArray<ArtifactReference>>(
                            ref reader,
                            options);
                    properties++;
                    break;
                default:
                    throw new JsonException(
                        string.Concat(
                            "Unknown artifact compatibility property: ",
                            property));
            }
        }

        if (properties != 5 ||
            dimensions.IsDefault ||
            migrations.IsDefault)
        {
            throw new JsonException(
                "Artifact compatibility requires every exact compatibility field.");
        }

        return new ArtifactCompatibility(
            policy,
            dimensions,
            readerRange,
            writerRange,
            migrations);
    }

    public override void Write(
        Utf8JsonWriter writer,
        ArtifactCompatibility value,
        JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WritePropertyName("policy");
        JsonSerializer.Serialize(writer, value.Policy, options);
        writer.WritePropertyName("dimensions");
        JsonSerializer.Serialize(writer, value.Dimensions, options);
        writer.WritePropertyName("readerRange");
        JsonSerializer.Serialize(writer, value.ReaderRange, options);
        writer.WritePropertyName("writerRange");
        JsonSerializer.Serialize(writer, value.WriterRange, options);
        writer.WritePropertyName("migrationReferences");
        JsonSerializer.Serialize(writer, value.MigrationReferences, options);
        writer.WriteEndObject();
    }
}
