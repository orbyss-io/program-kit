namespace Notes.Api.CreateNote;

public sealed record CreateNoteRequest(Guid OperationId, Guid NoteId, string Name);
