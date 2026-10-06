namespace Notes.Core;

public interface INoteAuthoring
{
    Task<NoteOutcome<NoteAcknowledgement>> CreateAsync(NoteOwner owner, Guid operationId, Guid noteId, string name, CancellationToken cancellation);
    Task<NoteOutcome<NoteAcknowledgement>> RenameAsync(NoteOwner owner, Guid operationId, Guid noteId, long expectedRevision, string name, CancellationToken cancellation);
}
