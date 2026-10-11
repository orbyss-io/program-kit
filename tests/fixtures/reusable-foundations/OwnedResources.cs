using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;
using Product.Core;

namespace Application.PostgreSql;

/// <summary>Application-owned PostgreSQL mapping, units and owner predicate.</summary>
public sealed class OwnedResources(IPostgreSqlUnitLeaseFactory<ApplicationDbContext> units) : IOwnedResources
{
    /// <inheritdoc />
    public async Task<CreateResourceOutcome> CreateAsync(Guid id, ResourceOwner owner, CancellationToken cancellationToken)
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        var changed = await context.Database.ExecuteSqlInterpolatedAsync(
            $"INSERT INTO owned_resource (id,issuer,subject) VALUES ({id},{owner.Issuer},{owner.Subject}) ON CONFLICT DO NOTHING", unit.Deadline.Token);
        return changed == 1 ? CreateResourceOutcome.Created : CreateResourceOutcome.Conflict;
    }
    /// <inheritdoc />
    public async Task<Guid?> ReadAsync(Guid id, ResourceOwner owner, CancellationToken cancellationToken)
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        var found = await context.Database.SqlQuery<Guid>(
            $"SELECT id AS \"Value\" FROM owned_resource WHERE id={id} AND issuer={owner.Issuer} AND subject={owner.Subject}").ToArrayAsync(unit.Deadline.Token);
        return found.Length == 1 ? found[0] : null;
    }
}
