namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationConditional;

internal sealed class ConditionalInvocationProbe
{
    internal string Run(bool selectFirst) =>
        (selectFirst ? new Version(1, 0) : new Version(2, 0)).ToString();
}
