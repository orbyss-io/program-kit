using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class LossyNumericDecimalConverter : JsonConverter<decimal>
{
    public override decimal Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options) =>
        reader.GetDecimal();

    public override void Write(
        Utf8JsonWriter writer,
        decimal value,
        JsonSerializerOptions options) =>
        writer.WriteNumberValue(value);
}
