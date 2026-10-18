namespace SnapshotLesson;

/// <summary>Preserves the scan alternative for one-shot or smaller immutable snapshots.</summary>
public sealed class SnapshotScan
{
    /// <summary>Owns a copy of the admitted snapshot rows.</summary>
    private readonly Note[] snapshot;

    /// <summary>Copies and validates snapshot entries without building an index.</summary>
    public SnapshotScan(IEnumerable<Note> notes)
    {
        ArgumentNullException.ThrowIfNull(notes);
        snapshot = notes.ToArray();
        foreach (var note in snapshot)
        {
            ArgumentNullException.ThrowIfNull(note);
            ArgumentNullException.ThrowIfNull(note.Id);
            ArgumentNullException.ThrowIfNull(note.Owner);
        }
    }

    /// <summary>Materializes an exact-owner result in original input order.</summary>
    public IReadOnlyList<Note> ForOwner(string owner)
    {
        ArgumentNullException.ThrowIfNull(owner);
        var result = new List<Note>();
        foreach (var note in snapshot)
        {
            if (StringComparer.Ordinal.Equals(note.Owner, owner)) result.Add(note);
        }
        return result.AsReadOnly();
    }
}
