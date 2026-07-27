namespace Orbyss.ProgramKit.Tasks.InProcess.Coordination;

internal interface IInProcessTaskRuntime
{
    bool IsStarted { get; }

    bool IsAccepting { get; }

    int QueueDepth { get; }

    int QueueCapacity { get; }

    ValueTask StartAsync(CancellationToken cancellationToken);

    ValueTask StopAsync(bool drain, CancellationToken cancellationToken);
}
