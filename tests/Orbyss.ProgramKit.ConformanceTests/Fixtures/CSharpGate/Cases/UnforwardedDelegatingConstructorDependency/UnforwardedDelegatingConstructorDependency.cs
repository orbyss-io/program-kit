namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.UnforwardedDelegatingConstructorDependency;

internal sealed class UnforwardedDelegatingConstructorDependency
{
    private readonly IUnforwardedHandler? handler;

    internal UnforwardedDelegatingConstructorDependency()
        : this(null)
    {
    }

    private UnforwardedDelegatingConstructorDependency(
        IUnforwardedHandler? handler)
    {
        this.handler = handler;
    }

    internal void Handle() => handler?.Handle();
}
