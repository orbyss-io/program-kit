using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Uses the same provider-owned mapping during EF authoring, deployment and runtime.</summary>
public sealed class NativeMigrationEntryConfiguration : IEntityTypeConfiguration<NativeMigrationEntry>
{
    /// <inheritdoc />
    public void Configure(EntityTypeBuilder<NativeMigrationEntry> builder)
    {
        builder.ToTable("ef_entries", "ef_example");
        builder.HasKey(entry => entry.Id);
        builder.Property(entry => entry.Value).IsRequired();
        builder.HasIndex(entry => entry.Value).IsUnique();
    }
}
