using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class BoundaryTokenConverter : JsonConverter<BoundaryToken>
{
    public override BoundaryToken Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => new(reader.GetString() ?? throw new JsonException("A token is required."));
    public override void Write(Utf8JsonWriter writer, BoundaryToken value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
