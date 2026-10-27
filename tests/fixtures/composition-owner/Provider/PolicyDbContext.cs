using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace Application.PostgreSql;

/// <summary>Owns the same native EF mapping during tooling and selected runtime activation.</summary>
public sealed class PolicyDbContext(DbContextOptions<PolicyDbContext> options) : FoundationPostgreSqlDbContext(options)
{
    /// <inheritdoc />
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var notes = modelBuilder.Entity<OwnedNoteRow>();
        notes.ToTable("owner_notes", "owner_example");
        notes.HasKey(nameof(OwnedNoteRow.Id));
        notes
            .Property(nameof(OwnedNoteRow.OwnerIssuer))
            .IsRequired()
            .UseCollation("C");
        notes
            .Property(nameof(OwnedNoteRow.OwnerSubject))
            .IsRequired()
            .UseCollation("C");
        notes
            .Property(nameof(OwnedNoteRow.Value))
            .IsRequired();
        notes
            .Property(nameof(OwnedNoteRow.Digest))
            .IsRequired();
    }
}
