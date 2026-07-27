namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ExceptionalConstructorDependency;

internal sealed class ExceptionalConstructorDependency
{
    private readonly IExceptionalHandler handler;

    internal ExceptionalConstructorDependency(IExceptionalHandler handler)
    {
        try
        {
            this.handler = handler;
        }
        catch (InvalidOperationException)
        {
            this.handler = handler;
        }
    }

    internal void Handle() => handler.Handle();
}
