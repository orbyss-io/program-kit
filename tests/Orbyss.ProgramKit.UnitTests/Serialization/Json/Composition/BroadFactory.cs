using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class BroadFactory : JsonConverterFactory
{
    private readonly List<Type> observedTypes = [];
    internal IReadOnlyList<Type> ObservedTypes => observedTypes;

    internal void ClearObservedTypes() => observedTypes.Clear();
    public override bool CanConvert(Type typeToConvert)
    {
        observedTypes.Add(typeToConvert);
        return true;
    }

    public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options) => typeToConvert == typeof(DeclaredFactoryValue) ? new DeclaredFactoryValueConverter() : throw new InvalidOperationException("The factory was invoked outside its declared target.");
}
