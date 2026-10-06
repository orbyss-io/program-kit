namespace Notes.Api.ListNotes;

public sealed record ListNotesResponse(IReadOnlyList<NoteWire> Items, Guid? NextAfterNoteId);
