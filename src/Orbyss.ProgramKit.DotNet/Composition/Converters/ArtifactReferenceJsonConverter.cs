using System.Text.Json;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

internal sealed class ArtifactReferenceJsonConverter :
    JsonConverter<ArtifactReference>
{
    public override ArtifactReference Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("An artifact reference must be an object.");
        }

        ProgramKitIdentifier identity = default;
        SemanticVersion version = default;
        Sha256Digest digest = default;
        var properties = 0;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException("An artifact reference property name is required.");
            }

            var property = reader.GetString();
            reader.Read();
            switch (property)
            {
                case "identity":
                    identity = JsonSerializer.Deserialize<ProgramKitIdentifier>(
                        ref reader,
                        options);
                    properties++;
                    break;
                case "version":
                    version = JsonSerializer.Deserialize<SemanticVersion>(
                        ref reader,
                        options);
                    properties++;
                    break;
                case "digest":
                    digest = JsonSerializer.Deserialize<Sha256Digest>(
                        ref reader,
                        options);
                    properties++;
                    break;
                default:
                    throw new JsonException(
                        string.Concat(
                            "Unknown artifact reference property: ",
                            property));
            }
        }

        if (properties != 3)
        {
            throw new JsonException(
                "An artifact reference requires identity, version, and digest.");
        }

        return new ArtifactReference(identity, version, digest);
    }

    public override void Write(
        Utf8JsonWriter writer,
        ArtifactReference value,
        JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WritePropertyName("identity");
        JsonSerializer.Serialize(writer, value.Identity, options);
        writer.WritePropertyName("version");
        JsonSerializer.Serialize(writer, value.Version, options);
        writer.WritePropertyName("digest");
        JsonSerializer.Serialize(writer, value.Digest, options);
        writer.WriteEndObject();
    }
}
