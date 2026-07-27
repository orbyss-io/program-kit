namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidDelegatingConstructorInjection;

internal sealed class DelegatingConstructorConsumer
{
    private readonly IDelegatingHandler handler;

    internal DelegatingConstructorConsumer(IDelegatingHandler handler)
        : this(handler, true)
    {
    }

    private DelegatingConstructorConsumer(
        IDelegatingHandler handler,
        bool _)
    {
        this.handler = handler;
    }

    internal void Handle() => handler.Handle();
}
