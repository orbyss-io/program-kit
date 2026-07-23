namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.InheritedBehaviorContract;

internal sealed class InheritedBehaviorValidator :
    InheritedBehaviorBase,
    IInheritedBehaviorValidator
{
    public bool Validate() => true;
}
