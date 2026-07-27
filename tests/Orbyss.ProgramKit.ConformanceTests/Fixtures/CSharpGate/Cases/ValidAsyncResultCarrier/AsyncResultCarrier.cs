namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidAsyncResultCarrier;

internal sealed class AsyncResultCarrier
{
    private readonly TaskCompletionSource<IAsyncResultRegistry> completion =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    internal bool Complete(IAsyncResultRegistry registry) =>
        completion.TrySetResult(registry);
}
