using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Profile-owned exact artifact-integrity JSON mechanics.</summary>
internal sealed class CommandArtifactIntegrityJsonConverter :
    JsonConverter<ArtifactIntegrity>
{
    public override ArtifactIntegrity Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("Artifact integrity must be an object.");
        }

        string? algorithm = null;
        Sha256Digest digest = default;
        var properties = 0;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException("An integrity property name is required.");
            }

            var property = reader.GetString();
            reader.Read();
            switch (property)
            {
                case "algorithm":
                    algorithm = reader.GetString();
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
                        string.Concat("Unknown integrity property: ", property));
            }
        }

        if (properties != 2 || string.IsNullOrWhiteSpace(algorithm))
        {
            throw new JsonException(
                "Artifact integrity requires algorithm and digest.");
        }

        return new ArtifactIntegrity(algorithm, digest);
    }

    public override void Write(
        Utf8JsonWriter writer,
        ArtifactIntegrity value,
        JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WriteString("algorithm", value.Algorithm);
        writer.WritePropertyName("digest");
        JsonSerializer.Serialize(writer, value.Digest, options);
        writer.WriteEndObject();
    }
}
