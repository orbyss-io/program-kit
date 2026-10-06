namespace Notes.Api.RenameNote;

public sealed record RenameNoteRequest(Guid OperationId, long ExpectedRevision, string Name);
