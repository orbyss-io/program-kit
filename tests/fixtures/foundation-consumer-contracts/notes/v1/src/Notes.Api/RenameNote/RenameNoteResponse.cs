namespace Notes.Api.RenameNote;

public sealed record RenameNoteResponse(Guid OperationId, NoteWire Note);
