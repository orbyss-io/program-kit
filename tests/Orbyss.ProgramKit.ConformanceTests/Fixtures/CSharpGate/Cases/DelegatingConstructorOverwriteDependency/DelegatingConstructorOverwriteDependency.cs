namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.DelegatingConstructorOverwriteDependency;

internal sealed class DelegatingConstructorOverwriteDependency
{
    private readonly IDelegatingOverwriteHandler? handler;

    internal DelegatingConstructorOverwriteDependency(
        IDelegatingOverwriteHandler handler,
        bool remove)
        : this(handler)
    {
        if (remove)
        {
            this.handler = null;
        }
    }

    private DelegatingConstructorOverwriteDependency(
        IDelegatingOverwriteHandler handler)
    {
        this.handler = handler;
    }

    internal void Handle() => handler?.Handle();
}
