using System.Threading;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Provider adapter; schema deployment belongs to an explicit preparation owner.</summary>
public sealed class PostgreSqlLabelStore<TContext>(IPostgreSqlUnitLeaseFactory<TContext> leases) : ILabelStore
    where TContext : FoundationPostgreSqlDbContext
{
    /// <inheritdoc />
    public async Task<string> ReadAsync(CancellationToken cancellationToken)
    {
        await using var unit = await leases.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        return await context.Database
            .SqlQueryRaw<string>("SELECT value AS \"Value\" FROM sample_labels WHERE id = 1")
            .SingleAsync(unit.Deadline.Token);
    }

    /// <inheritdoc />
    public async Task WriteAsync(string value, CancellationToken cancellationToken)
    {
        await using var unit = await leases.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        object[] parameters = [value];
        var affected = await context.Database.ExecuteSqlRawAsync(
            "UPDATE sample_labels SET value = {0}, revision = revision + 1 WHERE id = 1",
            parameters,
            unit.Deadline.Token
        );
        if (affected != 1)
            throw new System.InvalidOperationException("The explicitly prepared sample row is unavailable.");
    }
}
