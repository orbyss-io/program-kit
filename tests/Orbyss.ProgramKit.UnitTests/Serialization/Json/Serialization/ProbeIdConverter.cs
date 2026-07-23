using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class ProbeIdConverter : JsonConverter<ProbeId>
{
    public override ProbeId Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => new(reader.GetString() ?? throw new JsonException("Probe ID is required."));
    public override void Write(Utf8JsonWriter writer, ProbeId value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
