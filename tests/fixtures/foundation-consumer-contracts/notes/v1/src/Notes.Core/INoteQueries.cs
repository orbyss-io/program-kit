namespace Notes.Core;

public interface INoteQueries
{
    Task<NoteOutcome<NoteSnapshot>> ReadAsync(NoteOwner owner, Guid noteId, CancellationToken cancellation);
    Task<NoteOutcome<NotePage>> ListAsync(NoteOwner owner, Guid? afterNoteId, int size, CancellationToken cancellation);
}
