using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class NotSupportedReadModelConverter : JsonConverter<NotSupportedReadModel>
{
    public override NotSupportedReadModel? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => throw new NotSupportedException("Intentional read-side boundary probe.");
    public override void Write(Utf8JsonWriter writer, NotSupportedReadModel value, JsonSerializerOptions options) => writer.WriteStringValue(value.Value);
}
