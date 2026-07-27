namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.GenericConcreteRegistryReturn;

public interface IGenericRegistry<T>
{
    T? Current { get; }
}
