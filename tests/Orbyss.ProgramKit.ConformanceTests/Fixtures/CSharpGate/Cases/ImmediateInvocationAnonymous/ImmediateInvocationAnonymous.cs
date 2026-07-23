namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationAnonymous;

internal sealed class ImmediateInvocationAnonymous
{
    internal static string Run() =>
        new
        {
            Value = 1,
        }.ToString();
}
