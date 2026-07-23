namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.UnprovenancedInterfaceFieldDependency;

internal sealed class UnprovenancedInterfaceFieldDependency
{
    private readonly IUnprovenancedHandler? handler;

    internal object? Value => handler;
}
