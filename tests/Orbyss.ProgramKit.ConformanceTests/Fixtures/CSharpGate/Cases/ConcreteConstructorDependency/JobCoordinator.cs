namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ConcreteConstructorDependency;

public sealed class JobCoordinator
{
    public JobCoordinator(JobHandler handler)
    {
        Handler = handler;
    }

    public JobHandler Handler { get; }
}
