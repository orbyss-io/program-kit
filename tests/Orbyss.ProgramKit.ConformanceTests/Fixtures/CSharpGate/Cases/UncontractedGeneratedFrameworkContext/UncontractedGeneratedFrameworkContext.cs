using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.UncontractedGeneratedFrameworkContext;

[JsonSerializable(typeof(string))]
internal sealed partial class UncontractedGeneratedFrameworkContext :
    JsonSerializerContext
{
    public string Describe() => nameof(UncontractedGeneratedFrameworkContext);
}
