namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationUnary;

internal sealed class ImmediateInvocationUnary
{
    public static ImmediateInvocationUnary operator +(
        ImmediateInvocationUnary value) =>
        value;

    internal static void Run() =>
        (+new ImmediateInvocationUnary()).Execute();

    private void Execute()
    {
    }
}
