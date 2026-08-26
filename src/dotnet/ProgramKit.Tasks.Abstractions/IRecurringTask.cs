namespace ProgramKit.Tasks;

/// <summary>Runs periodically for one shell generation and once per host replica.</summary>
public interface IRecurringTask : IProgramKitTask
{
    TimeSpan Interval { get; }

    TimeSpan InitialDelay => TimeSpan.Zero;

    Task ExecuteAsync(CancellationToken cancellationToken);
}
