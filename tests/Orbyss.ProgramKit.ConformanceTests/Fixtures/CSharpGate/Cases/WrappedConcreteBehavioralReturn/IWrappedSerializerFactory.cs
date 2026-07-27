namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.WrappedConcreteBehavioralReturn;

public interface IWrappedSerializerFactory
{
    Task<WrappedSerializer> CreateAsync();
}
