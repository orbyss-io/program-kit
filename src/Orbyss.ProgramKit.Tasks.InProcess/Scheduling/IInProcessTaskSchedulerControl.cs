namespace Orbyss.ProgramKit.Tasks.InProcess.Scheduling;

internal interface IInProcessTaskSchedulerControl
{
    ValueTask StartAsync(CancellationToken cancellationToken);

    ValueTask StopAsync(CancellationToken cancellationToken);
}
