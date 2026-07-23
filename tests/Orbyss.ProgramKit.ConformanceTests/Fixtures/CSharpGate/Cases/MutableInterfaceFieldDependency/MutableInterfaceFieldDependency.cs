namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.MutableInterfaceFieldDependency;

internal sealed class MutableInterfaceFieldDependency
{
    private IMutableInterfaceFieldHandler _handler;

    internal MutableInterfaceFieldDependency(
        IMutableInterfaceFieldHandler handler)
    {
        _handler = handler;
    }

    internal void Handle() => _handler.Handle();
}
