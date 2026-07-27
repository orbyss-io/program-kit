namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidPrimaryConstructorDelegation;

internal sealed class PrimaryDelegatingConsumer(
    IPrimaryDelegatingHandler handler)
{
    private readonly IPrimaryDelegatingHandler handler = handler;

    internal PrimaryDelegatingConsumer(
        IPrimaryDelegatingHandler handler,
        bool _)
        : this(handler)
    {
    }

    internal void Handle() => handler.Handle();
}
