namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

public sealed class ConcreteTestDependency
{
    private readonly TestDependencyHandler handler;

    public ConcreteTestDependency(TestDependencyHandler handler)
    {
        this.handler = handler;
    }

    public void Run() => handler.Handle();
}
