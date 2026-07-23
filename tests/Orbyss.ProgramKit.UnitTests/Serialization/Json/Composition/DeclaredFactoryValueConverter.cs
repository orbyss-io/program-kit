using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class DeclaredFactoryValueConverter : JsonConverter<DeclaredFactoryValue>
{
    public override DeclaredFactoryValue Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => new(reader.GetString() ?? throw new JsonException("A declared value is required."));
    public override void Write(Utf8JsonWriter writer, DeclaredFactoryValue value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
