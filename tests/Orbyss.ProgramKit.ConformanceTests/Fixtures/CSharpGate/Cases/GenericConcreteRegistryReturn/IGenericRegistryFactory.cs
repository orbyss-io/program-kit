namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.GenericConcreteRegistryReturn;

public interface IGenericRegistryFactory
{
    GenericRegistry<T> Create<T>();
}
