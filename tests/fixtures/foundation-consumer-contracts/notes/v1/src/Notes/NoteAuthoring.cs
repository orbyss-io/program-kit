using Notes.Core;

namespace Notes;

/// <summary>Admits application commands before invoking the atomic revision capability.</summary>
internal sealed class NoteAuthoring(INoteRevisionLifecycle revisions) : INoteAuthoring
{
    public Task<NoteOutcome<NoteAcknowledgement>> CreateAsync(NoteOwner owner, Guid operationId, Guid noteId, string name, CancellationToken cancellation)
    {
        if (operationId == Guid.Empty || noteId == Guid.Empty) return Denied(NoteFailure.InvalidIdentity);
        if (!NoteName.TryCreate(name, out var admitted)) return Denied(NoteFailure.InvalidName);
        return revisions.CreateAsync(owner, operationId, noteId, admitted!, cancellation);
    }
    public Task<NoteOutcome<NoteAcknowledgement>> RenameAsync(NoteOwner owner, Guid operationId, Guid noteId, long expectedRevision, string name, CancellationToken cancellation)
    {
        if (operationId == Guid.Empty || noteId == Guid.Empty || expectedRevision < 1 || expectedRevision == long.MaxValue) return Denied(NoteFailure.InvalidIdentity);
        if (!NoteName.TryCreate(name, out var admitted)) return Denied(NoteFailure.InvalidName);
        return revisions.RenameAsync(owner, operationId, noteId, expectedRevision, admitted!, cancellation);
    }
    private static Task<NoteOutcome<NoteAcknowledgement>> Denied(NoteFailure failure) => Task.FromResult(NoteOutcome<NoteAcknowledgement>.Denied(failure));
}
