namespace ProgramKit.Tasks;

/// <summary>Runs once while a shell generation is activating.</summary>
public interface IStartupTask : IProgramKitTask
{
    Task ExecuteAsync(CancellationToken cancellationToken);
}
