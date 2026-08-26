using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace ProgramKit.Tasks;

internal sealed class ShellTaskManager(
    IServiceProvider serviceProvider,
    IEnumerable<IBackgroundTask> backgroundTasks,
    IEnumerable<IRecurringTask> recurringTasks,
    ILogger<ShellTaskManager> logger) : IShellTaskManager, IAsyncDisposable
{
    private readonly object sync = new();
    private readonly IReadOnlyList<IBackgroundTask> backgroundTasks = backgroundTasks.ToArray();
    private readonly IReadOnlyList<IRecurringTask> recurringTasks = recurringTasks.ToArray();
    private CancellationTokenSource? lifetimeCancellation;
    private IReadOnlyList<Task> runningTasks = [];
    private Task? stopTask;
    private bool started;

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        lock (sync)
        {
            if (started)
                throw new InvalidOperationException("Shell tasks cannot be started twice in the same shell generation.");

            started = true;
            lifetimeCancellation = new CancellationTokenSource();
        }

        try
        {
            await RunStartupTasksAsync(cancellationToken).ConfigureAwait(false);
            var token = lifetimeCancellation.Token;
            runningTasks =
            [
                .. backgroundTasks.Select(task => RunBackgroundTaskAsync(task, token)),
                .. recurringTasks.Select(task => RunRecurringTaskAsync(task, token))
            ];
        }
        catch
        {
            await StopAsync(CancellationToken.None).ConfigureAwait(false);
            throw;
        }
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        lock (sync)
        {
            stopTask ??= StopCoreAsync(cancellationToken);
            return stopTask;
        }
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync(CancellationToken.None).ConfigureAwait(false);
        lifetimeCancellation?.Dispose();
    }

    private async Task RunStartupTasksAsync(CancellationToken cancellationToken)
    {
        await using var scope = serviceProvider.CreateAsyncScope();
        foreach (var task in scope.ServiceProvider.GetServices<IStartupTask>())
        {
            logger.LogInformation("Starting shell startup task {TaskId}.", task.Id);
            await task.ExecuteAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private async Task RunBackgroundTaskAsync(IBackgroundTask task, CancellationToken cancellationToken)
    {
        try
        {
            logger.LogInformation("Starting shell background task {TaskId}.", task.Id);
            await task.ExecuteAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Shell background task {TaskId} faulted.", task.Id);
            throw;
        }
    }

    private async Task RunRecurringTaskAsync(IRecurringTask task, CancellationToken cancellationToken)
    {
        if (task.Interval <= TimeSpan.Zero)
            throw new InvalidOperationException($"Recurring task '{task.Id}' must declare a positive interval.");

        try
        {
            if (task.InitialDelay > TimeSpan.Zero)
                await Task.Delay(task.InitialDelay, cancellationToken).ConfigureAwait(false);

            using var timer = new PeriodicTimer(task.Interval);
            do
            {
                await task.ExecuteAsync(cancellationToken).ConfigureAwait(false);
            }
            while (await timer.WaitForNextTickAsync(cancellationToken).ConfigureAwait(false));
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Shell recurring task {TaskId} faulted.", task.Id);
            throw;
        }
    }

    private async Task StopCoreAsync(CancellationToken cancellationToken)
    {
        lifetimeCancellation?.Cancel();
        if (runningTasks.Count == 0)
            return;

        try
        {
            await Task.WhenAll(runningTasks).WaitAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "One or more shell tasks failed while the shell was draining.");
        }
    }
}
