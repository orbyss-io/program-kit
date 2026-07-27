namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ComputedInterfacePropertyDependency;

public sealed class ComputedInterfacePropertyDependency
{
    public IComputedValidator Validator => ResolveValidator();

    private static IComputedValidator ResolveValidator() =>
        throw new NotSupportedException();
}
