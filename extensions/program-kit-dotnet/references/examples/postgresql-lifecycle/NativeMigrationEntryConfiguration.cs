using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using System.Linq.Expressions;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Uses the same provider-owned mapping during EF authoring, deployment and runtime.</summary>
public sealed class NativeMigrationEntryConfiguration : IEntityTypeConfiguration<NativeMigrationEntry>
{
    /// <inheritdoc />
    public void Configure(EntityTypeBuilder<NativeMigrationEntry> builder)
    {
        builder.ToTable("ef_entries", "ef_example");
        Expression<Func<NativeMigrationEntry, object?>> key = entry => entry.Id;
        Expression<Func<NativeMigrationEntry, string>> value = entry => entry.Value;
        Expression<Func<NativeMigrationEntry, object?>> index = entry => entry.Value;
        builder.HasKey(key);
        builder
            .Property(value)
            .IsRequired();
        builder
            .HasIndex(index)
            .IsUnique();
    }
}
