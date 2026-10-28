using CShells.Lifecycle;
using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace Application.PostgreSql;

/// <summary>Reads native EF compatibility and privileges; it never creates schema or grants.</summary>
internal sealed class OwnedNotesAdmission(IPostgreSqlUnitLeaseFactory<PolicyDbContext> units, OwnedNoteSecret secret) : IShellInitializer
{
    /// <inheritdoc />
    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        _ = secret;
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        if (context.Database.HasPendingModelChanges()
            || (await context.Database.GetPendingMigrationsAsync(unit.Deadline.Token)).Any()
            || !(await context.Database.GetAppliedMigrationsAsync(unit.Deadline.Token)).Any())
            throw new InvalidOperationException("OWNER_SCHEMA_REQUIRED");
        const string privileges = """
            SELECT CASE WHEN has_schema_privilege(current_user,'owner_example','USAGE')
              AND NOT has_schema_privilege(current_user,'owner_example','CREATE')
              AND NOT has_schema_privilege(current_user,'public','CREATE')
              AND has_table_privilege(current_user,'owner_example.owner_notes','SELECT')
              AND has_table_privilege(current_user,'owner_example.owner_notes','INSERT')
              AND has_table_privilege(current_user,'public."__EFMigrationsHistory"','SELECT')
              AND NOT has_table_privilege(current_user,'public."__EFMigrationsHistory"','INSERT,UPDATE,DELETE')
              THEN 1 ELSE 0 END AS "Value"
            """;
        var query = context.Database.SqlQueryRaw<int>(privileges);
        if (await query.SingleAsync(unit.Deadline.Token) != 1) throw new InvalidOperationException("OWNER_GRANTS_REQUIRED");
    }
}
