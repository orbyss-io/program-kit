using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class DeclaredOnlyFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert) => typeToConvert == typeof(DeclaredFactoryValue);
    public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options) => new DeclaredFactoryValueConverter();
}
