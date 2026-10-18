using Microsoft.EntityFrameworkCore;

namespace ProgramKit.Examples.Evidence;

/// <summary>Provider-private relational model checked against independent accepted schema.</summary>
public sealed class EvidenceDbContext(DbContextOptions<EvidenceDbContext> options) : DbContext(options)
{
    /// <summary>Private records are queried only by the owning provider.</summary>
    internal DbSet<EvidenceRow> Entries => Set<EvidenceRow>();

    /// <inheritdoc />
    protected override void OnModelCreating(ModelBuilder model)
    {
        var entity = model.Entity<EvidenceRow>();
        entity
            .ToTable("entries", "evidence");
        entity
            .HasKey(row => row.Id);
        entity
            .Property(row => row.Id)
            .HasColumnName("identity");
        entity
            .Property(row => row.Owner)
            .HasColumnName("owner");
        entity
            .Property(row => row.Packet)
            .HasColumnName("packet")
            .HasColumnType("jsonb");
        entity
            .Property(row => row.Accepted)
            .HasColumnName("accepted");
        entity
            .Property(row => row.Revision)
            .HasColumnName("revision")
            .IsConcurrencyToken();
    }
}
