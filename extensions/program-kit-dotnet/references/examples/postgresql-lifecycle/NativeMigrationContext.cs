using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Owns the example's EF model and migrations without changing Foundation runtime lifetimes.</summary>
public sealed class NativeMigrationContext(DbContextOptions<NativeMigrationContext> options)
    : FoundationPostgreSqlDbContext(options)
{
    /// <inheritdoc />
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var configuration = new NativeMigrationEntryConfiguration();
        modelBuilder.ApplyConfiguration(configuration);
    }
}
