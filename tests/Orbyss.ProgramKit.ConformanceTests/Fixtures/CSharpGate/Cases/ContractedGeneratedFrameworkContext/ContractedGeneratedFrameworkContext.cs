using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractedGeneratedFrameworkContext;

[JsonSerializable(typeof(string))]
internal sealed partial class ContractedGeneratedFrameworkContext :
    JsonSerializerContext,
    IContractedGeneratedFrameworkContext
{
    public string Describe() => nameof(ContractedGeneratedFrameworkContext);
}
