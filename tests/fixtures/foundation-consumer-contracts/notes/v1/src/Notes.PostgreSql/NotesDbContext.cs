using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace Notes.PostgreSql;

internal sealed class NotesDbContext(DbContextOptions<NotesDbContext> options) : FoundationPostgreSqlDbContext(options)
{
    internal DbSet<NoteRow> Notes => Set<NoteRow>();
    internal DbSet<RevisionRow> Revisions => Set<RevisionRow>();
    internal DbSet<ReceiptRow> Receipts => Set<ReceiptRow>();

    protected override void OnModelCreating(ModelBuilder model)
    {
        model.Entity<NoteRow>(entity =>
        {
            entity.ToTable("notes");
            entity.HasKey(row => new { row.Issuer, row.Subject, row.Id }).HasName(StorageNames.NoteKey);
            entity.Property(row => row.Issuer).HasColumnName("issuer").UseCollation("C");
            entity.Property(row => row.Subject).HasColumnName("subject").UseCollation("C");
            entity.Property(row => row.Id).HasColumnName("id");
            entity.Property(row => row.Revision).HasColumnName("revision");
            entity.Property(row => row.Name).HasColumnName("name");
        });
        model.Entity<RevisionRow>(entity =>
        {
            entity.ToTable("note_revisions");
            entity.HasKey(row => new { row.Issuer, row.Subject, row.Id, row.Revision }).HasName(StorageNames.RevisionKey);
            entity.HasAlternateKey(row => new { row.Issuer, row.Subject, row.Id, row.Revision, row.Name })
                .HasName(StorageNames.RevisionSnapshotKey);
            entity.HasOne<NoteRow>().WithMany().HasForeignKey(row => new { row.Issuer, row.Subject, row.Id })
                .HasConstraintName(StorageNames.RevisionNoteForeignKey).OnDelete(DeleteBehavior.Restrict);
            entity.Property(row => row.Issuer).HasColumnName("issuer").UseCollation("C");
            entity.Property(row => row.Subject).HasColumnName("subject").UseCollation("C");
            entity.Property(row => row.Id).HasColumnName("id");
            entity.Property(row => row.Revision).HasColumnName("revision");
            entity.Property(row => row.Name).HasColumnName("name");
        });
        model.Entity<ReceiptRow>(entity =>
        {
            entity.ToTable("note_receipts");
            entity.HasKey(row => new { row.Issuer, row.Subject, row.OperationId }).HasName(StorageNames.ReceiptKey);
            entity.HasOne<RevisionRow>().WithMany().HasForeignKey(row => new { row.Issuer, row.Subject, row.Id, row.Revision, row.Name })
                .HasPrincipalKey(row => new { row.Issuer, row.Subject, row.Id, row.Revision, row.Name })
                .HasConstraintName(StorageNames.ReceiptRevisionForeignKey).OnDelete(DeleteBehavior.Restrict);
            entity.Property(row => row.Issuer).HasColumnName("issuer").UseCollation("C");
            entity.Property(row => row.Subject).HasColumnName("subject").UseCollation("C");
            entity.Property(row => row.OperationId).HasColumnName("operation_id");
            entity.Property(row => row.Digest).HasColumnName("digest");
            entity.Property(row => row.Id).HasColumnName("id");
            entity.Property(row => row.Revision).HasColumnName("revision");
            entity.Property(row => row.Name).HasColumnName("name");
        });
    }
}
