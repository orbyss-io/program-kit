namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ConstrainedConcreteConstructorDependency;

internal sealed class ConstrainedConcreteConstructorDependency<T>
    where T : ConstrainedConcreteHandler
{
    internal ConstrainedConcreteConstructorDependency(T handler)
    {
        ArgumentNullException.ThrowIfNull(handler);
    }
}
