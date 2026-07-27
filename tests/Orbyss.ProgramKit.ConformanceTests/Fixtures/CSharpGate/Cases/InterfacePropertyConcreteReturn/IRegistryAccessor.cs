namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.InterfacePropertyConcreteReturn;

public interface IRegistryAccessor
{
    LeakedRegistry Current { get; }

    LeakedRegistry this[int index] { get; }
}
