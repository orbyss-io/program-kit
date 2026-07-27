namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ConcreteFieldDependency;

internal sealed class ConcreteFieldDependency
{
    private ConcreteFieldHandler? _handler = null;

    internal bool HasHandler() => _handler is not null;
}
