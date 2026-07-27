namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.BehavioralResultReturn;

internal sealed record BehavioralResult(bool Succeeded) : IBehavioralResult
{
    public void Execute()
    {
    }
}
