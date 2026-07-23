namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.BehavioralResultReturn;

internal interface IBehavioralResult
{
    bool Succeeded { get; }

    void Execute();
}
