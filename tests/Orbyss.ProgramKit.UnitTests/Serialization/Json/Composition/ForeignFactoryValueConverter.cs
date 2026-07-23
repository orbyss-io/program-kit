using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class ForeignFactoryValueConverter : JsonConverter<ForeignFactoryValue>
{
    public override ForeignFactoryValue Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => new(reader.GetString() ?? throw new JsonException("A foreign value is required."));
    public override void Write(Utf8JsonWriter writer, ForeignFactoryValue value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
