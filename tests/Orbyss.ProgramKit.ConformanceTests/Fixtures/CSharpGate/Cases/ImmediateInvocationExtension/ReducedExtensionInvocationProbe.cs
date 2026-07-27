namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationExtension;

internal sealed class ReducedExtensionInvocationProbe
{
    internal int InvocationCount { get; private set; }

    internal void Run()
    {
        InvocationCount++;
        new object().Invoke();
    }
}
