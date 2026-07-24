using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

internal sealed class JsonSerializationProfileRefJsonConverter :
    JsonConverter<JsonSerializationProfileRef>
{
    public override JsonSerializationProfileRef Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var reference = JsonReferenceConverterMechanics.Read(
            ref reader,
            options,
            "JSON serialization profile");
        return new JsonSerializationProfileRef(
            reference.Identity,
            reference.Version,
            reference.Digest);
    }

    public override void Write(
        Utf8JsonWriter writer,
        JsonSerializationProfileRef value,
        JsonSerializerOptions options) =>
        JsonReferenceConverterMechanics.Write(
            writer,
            value.Identity,
            value.Version,
            value.Digest,
            options);
}
