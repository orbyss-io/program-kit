namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationSwitch;

internal sealed class ImmediateInvocationSwitch
{
    internal static void Run() =>
        (new ImmediateInvocationSwitch() switch
        {
            var value => value,
        }).Execute();

    private void Execute()
    {
    }
}
