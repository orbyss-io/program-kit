namespace Notes.Core;

/// <summary>Pages notes by stable note identity without exposing provider query machinery.</summary>
public sealed class NotePage
{
    public NotePage(IReadOnlyList<NoteSnapshot> items, Guid? nextAfterNoteId)
    {
        ArgumentNullException.ThrowIfNull(items);
        var owned = new NoteSnapshot[items.Count];
        for (var index = 0; index < owned.Length; index++)
            owned[index] = items[index] ?? throw new ArgumentException("A page cannot contain a null note.", nameof(items));
        Items = Array.AsReadOnly(owned);
        NextAfterNoteId = nextAfterNoteId;
    }
    public IReadOnlyList<NoteSnapshot> Items { get; }
    public Guid? NextAfterNoteId { get; }
}
