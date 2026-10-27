using CShells.Lifecycle;
using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Admits the shell through read-only EF history, model and runtime privilege checks.</summary>
public sealed class NativeMigrationAdmission(IPostgreSqlUnitLeaseFactory<NativeMigrationContext> units) : IShellInitializer
{
    /// <inheritdoc />
    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        if (context.Database.HasPendingModelChanges()
            || (await context.Database.GetPendingMigrationsAsync(unit.Deadline.Token)).Any()
            || !(await context.Database.GetAppliedMigrationsAsync(unit.Deadline.Token)).Any())
            throw new InvalidOperationException("Deploy the required EF migration before runtime admission.");
        const string requiredPrivileges = """
            SELECT CASE WHEN
              has_schema_privilege(current_user,'ef_example','USAGE')
              AND NOT has_schema_privilege(current_user,'ef_example','CREATE')
              AND has_table_privilege(current_user,'ef_example.ef_entries','SELECT')
              AND has_table_privilege(current_user,'ef_example.ef_entries','INSERT')
              AND has_table_privilege(current_user,'ef_example.ef_entries','UPDATE')
              AND has_table_privilege(current_user,'ef_example.ef_entries','DELETE')
              AND has_table_privilege(current_user,'ef_example."__EFMigrationsHistory"','SELECT')
              AND NOT has_table_privilege(current_user,'ef_example."__EFMigrationsHistory"','INSERT,UPDATE,DELETE')
              AND has_sequence_privilege(current_user,pg_get_serial_sequence('ef_example.ef_entries','Id'),'USAGE')
              AND has_sequence_privilege(current_user,pg_get_serial_sequence('ef_example.ef_entries','Id'),'SELECT')
              THEN 1 ELSE 0 END AS "Value"
            """;
        var query = context.Database.SqlQueryRaw<int>(requiredPrivileges);
        var admitted = await query.SingleAsync(unit.Deadline.Token);
        if (admitted != 1) throw new InvalidOperationException("Required runtime privileges are unavailable.");
    }
}
