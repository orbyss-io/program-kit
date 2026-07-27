using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class ProbeConverterFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert) => typeToConvert == typeof(FactoryValue);
    public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options) => new FactoryValueConverter();
}
