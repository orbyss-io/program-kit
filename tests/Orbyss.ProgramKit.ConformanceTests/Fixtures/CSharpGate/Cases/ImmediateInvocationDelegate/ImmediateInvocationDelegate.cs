namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationDelegate;

internal sealed class ImmediateInvocationDelegate
{
    internal static void Run() =>
        ((Action)new ImmediateInvocationDelegate().Execute)();

    private void Execute()
    {
    }
}
