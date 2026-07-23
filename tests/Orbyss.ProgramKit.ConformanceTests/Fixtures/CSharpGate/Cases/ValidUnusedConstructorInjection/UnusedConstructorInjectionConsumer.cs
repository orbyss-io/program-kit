namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidUnusedConstructorInjection;

internal sealed class UnusedConstructorInjectionConsumer
{
    internal UnusedConstructorInjectionConsumer(IUnusedHandler handler)
    {
        Handler = handler;
    }

    internal IUnusedHandler Handler { get; }
}
