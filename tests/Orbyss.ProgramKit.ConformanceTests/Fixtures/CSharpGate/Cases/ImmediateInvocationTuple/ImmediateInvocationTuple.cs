namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationTuple;

internal sealed class ImmediateInvocationTuple
{
    internal static void Run() =>
        (new ImmediateInvocationTuple(), 0).Item1.Execute();

    private void Execute()
    {
    }
}
