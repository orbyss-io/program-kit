namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.MutableResultReturn;

internal sealed record MutableResult : IMutableResult
{
    public bool Succeeded { get; set; }
}
