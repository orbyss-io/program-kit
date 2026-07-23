namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationDynamic;

internal sealed class DynamicInvocationProbe
{
    internal string Run() =>
        ((dynamic)new object()).ToString();
}
