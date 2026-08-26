namespace ProgramKit.Tasks;

/// <summary>
/// Runs for the lifetime of one shell generation. The returned task must represent the complete operation.
/// </summary>
public interface IBackgroundTask : IProgramKitTask
{
    Task ExecuteAsync(CancellationToken cancellationToken);
}
