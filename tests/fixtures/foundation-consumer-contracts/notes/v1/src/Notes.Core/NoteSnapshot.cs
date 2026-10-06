namespace Notes.Core;

public sealed record NoteSnapshot(Guid Id, long Revision, NoteName Name);
