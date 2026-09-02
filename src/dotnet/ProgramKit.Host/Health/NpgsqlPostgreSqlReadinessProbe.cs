using Npgsql;

namespace ProgramKit.Host.Health;

/// <summary>Uses Npgsql to execute the fixed operational PostgreSQL readiness query.</summary>
internal sealed class NpgsqlPostgreSqlReadinessProbe(IConfiguration configuration) : IPostgreSqlReadinessProbe
{
    /// <inheritdoc />
    public async Task ProbeAsync(CancellationToken cancellationToken)
    {
        var connectionName = configuration["ProgramKit:Readiness:PostgreSql:ConnectionStringName"]!;
        var connectionString = configuration.GetConnectionString(connectionName)!;
        await using var connection = new NpgsqlConnection(connectionString);
        using var budget = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        budget.CancelAfter(TimeSpan.FromSeconds(3));
        await connection.OpenAsync(budget.Token).ConfigureAwait(false);
        await using var command = new NpgsqlCommand("SELECT 1", connection);
        await command.ExecuteScalarAsync(budget.Token).ConfigureAwait(false);
    }
}
