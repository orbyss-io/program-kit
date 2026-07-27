namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.GenericConcreteRegistryReturn;

public sealed class GenericRegistry<T> : IGenericRegistry<T>
{
    public T? Current => default;
}
