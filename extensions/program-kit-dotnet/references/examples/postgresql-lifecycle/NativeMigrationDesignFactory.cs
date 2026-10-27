using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
using Npgsql.EntityFrameworkCore.PostgreSQL.Infrastructure;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Creates only EF tooling contexts; runtime uses Foundation's registered tracked units.</summary>
public sealed class NativeMigrationDesignFactory : IDesignTimeDbContextFactory<NativeMigrationContext>
{
    /// <inheritdoc />
    public NativeMigrationContext CreateDbContext(string[] args)
    {
        // Model authoring needs no live server. Deployment supplies its own identity explicitly.
        var connection = Environment.GetEnvironmentVariable("PK_FIXTURE_EF_DEPLOYMENT")
            ?? "Host=127.0.0.1;Port=1;Database=design_only;Username=design_only;Timeout=1";
        var builder = new DbContextOptionsBuilder<NativeMigrationContext>();
        var options = builder
            .UseNpgsql(connection, ConfigureMigrations)
            .Options;
        return new NativeMigrationContext(options);
    }

    /// <summary>Retains the native migration history table in the example's owned schema.</summary>
    private static void ConfigureMigrations(NpgsqlDbContextOptionsBuilder provider)
        => provider.MigrationsHistoryTable("__EFMigrationsHistory", "ef_example");
}
