namespace ProgramKit.Host.Health;

/// <summary>Probes the configured operational PostgreSQL dependency without exposing connection details.</summary>
internal interface IPostgreSqlReadinessProbe
{
    /// <summary>Throws a transient dependency exception when PostgreSQL is not ready.</summary>
    Task ProbeAsync(CancellationToken cancellationToken);
}
