using Orbyss.ProgramKit.Tasks.Coordination;
using Orbyss.ProgramKit.Tasks.InProcess.Scheduling;

namespace Orbyss.ProgramKit.Tasks.InProcess.Coordination;

internal sealed class InProcessTaskRuntimeControl : ITaskRuntimeControl
{
    private readonly IInProcessTaskRuntime runtime;
    private readonly IInProcessTaskSchedulerControl scheduler;

    public InProcessTaskRuntimeControl(
        IInProcessTaskRuntime runtime,
        IInProcessTaskSchedulerControl scheduler)
    {
        this.runtime = runtime ??
            throw new ArgumentNullException(nameof(runtime));
        this.scheduler = scheduler ??
            throw new ArgumentNullException(nameof(scheduler));
    }

    public bool IsStarted => runtime.IsStarted;

    public bool IsAccepting => runtime.IsAccepting;

    public int QueueDepth => runtime.QueueDepth;

    public int QueueCapacity => runtime.QueueCapacity;

    public async ValueTask StartAsync(CancellationToken cancellationToken)
    {
        await runtime.StartAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            await scheduler.StartAsync(cancellationToken).ConfigureAwait(false);
        }
        catch
        {
            await runtime.StopAsync(
                drain: false,
                CancellationToken.None).ConfigureAwait(false);
            throw;
        }
    }

    public async ValueTask StopAsync(
        bool drain,
        CancellationToken cancellationToken)
    {
        await scheduler.StopAsync(cancellationToken).ConfigureAwait(false);
        await runtime.StopAsync(drain, cancellationToken).ConfigureAwait(false);
    }
}
