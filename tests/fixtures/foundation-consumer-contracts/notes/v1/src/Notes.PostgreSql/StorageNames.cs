namespace Notes.PostgreSql;

internal static class StorageNames
{
    internal const string Policy = "notes";
    internal const string NoteKey = "pk_notes";
    internal const string RevisionKey = "pk_note_revisions";
    internal const string ReceiptKey = "pk_note_receipts";
    internal const string RevisionSnapshotKey = "uq_note_revision_snapshot";
    internal const string RevisionNoteForeignKey = "fk_revision_note";
    internal const string ReceiptRevisionForeignKey = "fk_receipt_revision";
    internal const string UniqueViolation = "23505";
}
