namespace Notes.Core;

/// <summary>Owns atomic revision and receipt semantics, independently of the selected provider.</summary>
public interface INoteRevisionLifecycle
{
    Task<NoteOutcome<NoteAcknowledgement>> CreateAsync(NoteOwner owner, Guid operationId, Guid noteId, NoteName name, CancellationToken cancellation);
    Task<NoteOutcome<NoteAcknowledgement>> RenameAsync(NoteOwner owner, Guid operationId, Guid noteId, long expectedRevision, NoteName name, CancellationToken cancellation);
}
