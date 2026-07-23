using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class ThrowingCanConvertFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert) =>
        throw new InvalidOperationException(
            "The test factory failed during CanConvert.");

    public override JsonConverter CreateConverter(
        Type typeToConvert,
        JsonSerializerOptions options) =>
        throw new InvalidOperationException(
            "The test factory must not create a converter.");
}
