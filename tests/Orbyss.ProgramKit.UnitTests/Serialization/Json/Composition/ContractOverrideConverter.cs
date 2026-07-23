using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class ContractOverrideConverter : JsonConverter<ContractOverrideValue>
{
    public override ContractOverrideValue Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => new(reader.GetString() ?? throw new JsonException("A contract value is required."));
    public override void Write(Utf8JsonWriter writer, ContractOverrideValue value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
