namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.EarlyReturnConstructorDependency;

internal sealed class EarlyReturnConstructorDependency
{
    private readonly IEarlyReturnHandler? handler;

    internal EarlyReturnConstructorDependency(
        IEarlyReturnHandler handler,
        bool returnBeforeAssignment)
    {
        if (returnBeforeAssignment)
        {
            return;
        }

        this.handler = handler;
    }

    internal void Handle() => handler?.Handle();
}
