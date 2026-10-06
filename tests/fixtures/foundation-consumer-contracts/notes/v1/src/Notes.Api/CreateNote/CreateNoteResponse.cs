namespace Notes.Api.CreateNote;

public sealed record CreateNoteResponse(Guid OperationId, NoteWire Note);
