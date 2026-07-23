using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class IdentifierReplacementConverter : JsonConverter<ProgramKitIdentifier>
{
    public override ProgramKitIdentifier Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => new(reader.GetString() ?? throw new JsonException("An identifier is required."));
    public override void Write(Utf8JsonWriter writer, ProgramKitIdentifier value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
