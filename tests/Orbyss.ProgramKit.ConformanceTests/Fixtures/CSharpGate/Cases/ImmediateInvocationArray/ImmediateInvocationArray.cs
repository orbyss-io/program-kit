namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationArray;

internal sealed class ImmediateInvocationArray
{
    internal static void Run() =>
        (new[] { new ImmediateInvocationArray() })[0].Execute();

    private void Execute()
    {
    }
}
