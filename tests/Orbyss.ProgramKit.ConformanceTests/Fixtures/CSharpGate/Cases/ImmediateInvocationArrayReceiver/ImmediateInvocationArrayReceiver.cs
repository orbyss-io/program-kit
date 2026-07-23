namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationArrayReceiver;

internal sealed class ImmediateInvocationArrayReceiver
{
    internal static object Run() =>
        new ImmediateInvocationArrayReceiver[0].Clone();
}
