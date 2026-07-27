namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractReturns;

internal sealed class OperationDescriptor : IOperationDescriptor
{
    public OperationDescriptor(string name)
    {
        Name = name;
    }

    public string Name { get; }
}
