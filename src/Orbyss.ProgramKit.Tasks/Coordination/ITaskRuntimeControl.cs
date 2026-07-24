namespace Orbyss.ProgramKit.Tasks.Coordination;

/// <summary>Controls one selected task runtime for a Generic Host adapter.</summary>
public interface ITaskRuntimeControl
{
    /// <summary>Gets whether worker loops have started.</summary>
    bool IsStarted { get; }

    /// <summary>Gets whether new background work is accepted.</summary>
    bool IsAccepting { get; }

    /// <summary>Gets the current accepted queue depth.</summary>
    int QueueDepth { get; }

    /// <summary>Gets the selected bounded queue capacity.</summary>
    int QueueCapacity { get; }

    /// <summary>Starts bounded worker loops.</summary>
    ValueTask StartAsync(CancellationToken cancellationToken);

    /// <summary>Stops acceptance and either drains or cancels accepted work.</summary>
    ValueTask StopAsync(
        bool drain,
        CancellationToken cancellationToken);
}
