using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Contributions;

namespace Orbyss.ProgramKit.DotNet.Composition.Converters;

internal sealed class JsonSerializationContributionRefJsonConverter :
    JsonConverter<JsonSerializationContributionRef>
{
    public override JsonSerializationContributionRef Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var reference = JsonReferenceConverterMechanics.Read(
            ref reader,
            options,
            "JSON serialization contribution");
        return new JsonSerializationContributionRef(
            reference.Identity,
            reference.Version,
            reference.Digest);
    }

    public override void Write(
        Utf8JsonWriter writer,
        JsonSerializationContributionRef value,
        JsonSerializerOptions options) =>
        JsonReferenceConverterMechanics.Write(
            writer,
            value.Identity,
            value.Version,
            value.Digest,
            options);
}
