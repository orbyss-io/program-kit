namespace ProgramKit.Host.Health;

/// <summary>Continuously probes an explicitly configured operational PostgreSQL dependency.</summary>
internal sealed class PostgreSqlReadinessService(
    PostgreSqlReadinessState state,
    IPostgreSqlReadinessProbe probe,
    ILogger<PostgreSqlReadinessService> logger) : BackgroundService
{
    /// <inheritdoc />
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(5));
        do
        {
            await ProbeOnceAsync(stoppingToken).ConfigureAwait(false);
        }
        while (await timer.WaitForNextTickAsync(stoppingToken).ConfigureAwait(false));
    }

    /// <summary>Runs one dependency probe and applies its redacted readiness transition.</summary>
    internal async Task ProbeOnceAsync(CancellationToken cancellationToken)
    {
        try
        {
            await probe.ProbeAsync(cancellationToken).ConfigureAwait(false);
            state.Set(true);
        }
        catch (Exception exception) when (
            !cancellationToken.IsCancellationRequested
            && exception is Npgsql.NpgsqlException or TimeoutException or OperationCanceledException)
        {
            _ = exception;
            state.Set(false);
            logger.LogWarning("Operational PostgreSQL readiness probe is not ready.");
        }
    }
}
