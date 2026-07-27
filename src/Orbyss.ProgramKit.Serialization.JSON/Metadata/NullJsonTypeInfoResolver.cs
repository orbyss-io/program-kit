using System.Text.Json;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Metadata;

internal sealed class NullJsonTypeInfoResolver : IJsonTypeInfoResolver
{
    internal NullJsonTypeInfoResolver()
    {
    }

    public JsonTypeInfo? GetTypeInfo(Type type, JsonSerializerOptions options) => null;
}
