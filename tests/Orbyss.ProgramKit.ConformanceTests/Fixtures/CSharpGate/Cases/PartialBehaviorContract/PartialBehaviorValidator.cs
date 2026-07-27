namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.PartialBehaviorContract;

internal sealed class PartialBehaviorValidator : IPartialBehaviorValidator
{
    public bool Enabled => true;

    public bool Validate() => true;
}
