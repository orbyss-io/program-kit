using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class RejectingOpenGenericListFactory : JsonConverterFactory
{
    private readonly List<Type> observedTypes = [];

    internal IReadOnlyList<Type> ObservedTypes => observedTypes;

    public override bool CanConvert(Type typeToConvert)
    {
        observedTypes.Add(typeToConvert);
        return false;
    }

    public override JsonConverter CreateConverter(
        Type typeToConvert,
        JsonSerializerOptions options) =>
        throw new InvalidOperationException(
            "A rejected target must fall through to source-generated metadata.");
}
