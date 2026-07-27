using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.LeakyFrameworkFactory;

internal sealed class LeakyFrameworkFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert) => false;

    public override JsonConverter CreateConverter(
        Type typeToConvert,
        JsonSerializerOptions options) =>
        throw new NotSupportedException();

    public void Reconfigure()
    {
        _ = GetType();
    }
}
