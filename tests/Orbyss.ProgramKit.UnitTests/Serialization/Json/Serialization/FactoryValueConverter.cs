using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class FactoryValueConverter : JsonConverter<FactoryValue>
{
    public override FactoryValue Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options) =>
        new(
            reader.GetString() ??
            throw new JsonException("Factory value is required."));

    public override void Write(
        Utf8JsonWriter writer,
        FactoryValue value,
        JsonSerializerOptions options) =>
        writer.WriteStringValue(value.Value);
}
