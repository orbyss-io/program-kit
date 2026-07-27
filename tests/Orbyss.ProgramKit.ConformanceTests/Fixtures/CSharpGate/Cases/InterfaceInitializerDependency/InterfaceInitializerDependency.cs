namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.InterfaceInitializerDependency;

internal sealed class InterfaceInitializerDependency
{
    internal IInitializerValidator Validator { get; } = ResolveValidator();

    private static IInitializerValidator ResolveValidator() =>
        throw new NotSupportedException();
}
