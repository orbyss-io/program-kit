namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractReturns;

internal interface IContractBuilder
{
    IContractBuilder Add();

    IContractRegistry Freeze();
}
