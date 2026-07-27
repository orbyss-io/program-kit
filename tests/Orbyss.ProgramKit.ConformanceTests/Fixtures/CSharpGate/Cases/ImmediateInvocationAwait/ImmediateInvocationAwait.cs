using System.Runtime.CompilerServices;

namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationAwait;

internal sealed class ImmediateInvocationAwait : INotifyCompletion
{
    public bool IsCompleted => true;

    public ImmediateInvocationAwait GetAwaiter() => this;

    public ImmediateInvocationAwait GetResult() => this;

    public void OnCompleted(Action continuation) => continuation();

    internal static async Task Run() =>
        (await new ImmediateInvocationAwait()).Execute();

    private void Execute()
    {
    }
}
