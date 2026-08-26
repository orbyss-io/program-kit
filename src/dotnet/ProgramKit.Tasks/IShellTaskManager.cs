namespace ProgramKit.Tasks;

public interface IShellTaskManager
{
    Task StartAsync(CancellationToken cancellationToken);

    Task StopAsync(CancellationToken cancellationToken);
}
