using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class FixedOwnedStateConverter : JsonConverter<FixedOwnedState>
{
    public override FixedOwnedState Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => reader.GetString() == "ready" ? FixedOwnedState.Ready : throw new JsonException("Unknown fixed-owned state.");
    public override void Write(Utf8JsonWriter writer, FixedOwnedState value, JsonSerializerOptions options) => writer.WriteStringValue(value == FixedOwnedState.Ready ? "ready" : throw new JsonException("Unknown fixed-owned state."));
}
