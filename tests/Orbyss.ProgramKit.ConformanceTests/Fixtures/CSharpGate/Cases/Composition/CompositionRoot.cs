namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.Composition;

public sealed class CompositionRoot
{
    private readonly CompositionHandler handler;

    public CompositionRoot(CompositionHandler handler)
    {
        this.handler = handler;
    }

    public void Run() => handler.Handle();
}
