namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ConditionalConstructorDependency;

internal sealed class ConditionalConstructorDependency
{
    private readonly IConditionalHandler? handler;

    internal ConditionalConstructorDependency(
        IConditionalHandler handler,
        bool assign)
    {
        if (assign)
        {
            this.handler = handler;
        }
    }

    internal void Handle() => handler?.Handle();
}
