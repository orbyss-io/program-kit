namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocation;

public sealed class ImmediateInvocationProbe
{
    public string Execute() => new object().ToString();
}
