namespace Notes.Core;

/// <summary>Retains the original immutable result of an exact operation replay.</summary>
public sealed record NoteAcknowledgement(Guid OperationId, NoteSnapshot Note);
