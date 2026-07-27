using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization.Converters;

internal sealed class CommandCSharpGateModelJsonConverter<TModel> :
    JsonConverter<TModel>
{
    public override TModel? Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options) =>
        JsonSerializer.Deserialize<TModel>(
            ref reader,
            WireOptions(options));

    public override void Write(
        Utf8JsonWriter writer,
        TModel value,
        JsonSerializerOptions options) =>
        JsonSerializer.Serialize(
            writer,
            value,
            WireOptions(options));

    private static JsonSerializerOptions WireOptions(JsonSerializerOptions options)
    {
        JsonSerializerOptions wire = new(options)
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            TypeInfoResolver = CSharpGateWireJsonContext.Default,
        };
        for (var index = wire.Converters.Count - 1; index >= 0; index--)
        {
            if (wire.Converters[index] is
                CommandCSharpGateModelJsonConverter<TModel>)
            {
                wire.Converters.RemoveAt(index);
            }
        }

        return wire;
    }
}
