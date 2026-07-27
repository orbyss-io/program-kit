namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractReturns;

internal sealed class ContractBuilder : IContractBuilder
{
    private readonly IContractRegistry registry;

    public ContractBuilder(IContractRegistry registry)
    {
        this.registry = registry;
    }

    public IContractBuilder Add() => this;

    public IContractRegistry Freeze() => registry;
}
