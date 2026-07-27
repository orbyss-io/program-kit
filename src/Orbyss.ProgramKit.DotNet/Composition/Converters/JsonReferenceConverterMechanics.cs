using System.Text.Json;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

internal static class JsonReferenceConverterMechanics
{
    internal static ArtifactReference Read(
        ref Utf8JsonReader reader,
        JsonSerializerOptions options,
        string description)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException(
                string.Concat(description, " reference must be an object."));
        }

        ProgramKitIdentifier identity = default;
        SemanticVersion version = default;
        Sha256Digest digest = default;
        var properties = 0;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException(
                    string.Concat(
                        description,
                        " reference property name is required."));
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
                            "Unknown ",
                            description,
                            " reference property: ",
                            property));
            }
        }

        if (properties != 3)
        {
            throw new JsonException(
                string.Concat(
                    description,
                    " requires identity, version, and digest."));
        }

        return new ArtifactReference(identity, version, digest);
    }

    internal static void Write(
        Utf8JsonWriter writer,
        ProgramKitIdentifier identity,
        SemanticVersion version,
        Sha256Digest digest,
        JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WritePropertyName("identity");
        JsonSerializer.Serialize(writer, identity, options);
        writer.WritePropertyName("version");
        JsonSerializer.Serialize(writer, version, options);
        writer.WritePropertyName("digest");
        JsonSerializer.Serialize(writer, digest, options);
        writer.WriteEndObject();
    }
}
