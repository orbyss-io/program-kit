namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractReturns;

internal interface IWrappedContractFactory
{
    Task<IContractRegistry> CreateAsync();

    IReadOnlyList<IContractRegistry> Registries { get; }

    IContractRegistry this[int index] { get; }
}
