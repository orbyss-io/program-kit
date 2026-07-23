namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ConcreteRegistryDependency;

public sealed class RegistryConsumer
{
    private readonly DependencyRegistry registry;

    public RegistryConsumer(DependencyRegistry registry)
    {
        this.registry = registry;
    }

    public int Count => registry.Count;
}
