namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidConditionalConstructorInjection;

internal sealed class ConditionalConstructorConsumer
{
    private readonly IConditionalHandler handler;

    internal ConditionalConstructorConsumer(
        IConditionalHandler preferred,
        IConditionalHandler fallback,
        bool usePreferred)
    {
        if (usePreferred)
        {
            handler = preferred;
        }
        else
        {
            handler = fallback;
        }
    }

    internal void Handle() => handler.Handle();
}
