using System.Collections.ObjectModel;

namespace SnapshotLesson;

/// <summary>Indexes an accepted immutable snapshot for repeated exact-owner queries.</summary>
public sealed class SnapshotQuery
{
    /// <summary>Owns read-only groups under ordinal owner identities.</summary>
    private readonly Dictionary<string, ReadOnlyCollection<Note>> byOwner;

    /// <summary>Copies admitted rows, preserving order and duplicate entries.</summary>
    public SnapshotQuery(IEnumerable<Note> notes)
    {
        ArgumentNullException.ThrowIfNull(notes);
        var groups = new Dictionary<string, List<Note>>(StringComparer.Ordinal);
        foreach (var note in notes)
        {
            ArgumentNullException.ThrowIfNull(note);
            ArgumentNullException.ThrowIfNull(note.Id);
            ArgumentNullException.ThrowIfNull(note.Owner);
            if (!groups.TryGetValue(note.Owner, out var owned))
            {
                owned = [];
                groups.Add(note.Owner, owned);
            }
            owned.Add(note);
        }
        byOwner = new Dictionary<string, ReadOnlyCollection<Note>>(StringComparer.Ordinal);
        foreach (var (owner, group) in groups)
        {
            var rows = group.ToArray();
            var readOnly = Array.AsReadOnly(rows);
            byOwner.Add(owner, readOnly);
        }
    }

    /// <summary>Returns an immutable owner group, or an empty result for an absent owner.</summary>
    public IReadOnlyList<Note> ForOwner(string owner)
    {
        ArgumentNullException.ThrowIfNull(owner);
        return byOwner.TryGetValue(owner, out var notes) ? notes : Array.Empty<Note>();
    }
}
