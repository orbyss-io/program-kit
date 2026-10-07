using Notes.Core;

namespace Notes.Api;

public sealed record NoteWire(Guid Id, long Revision, string Name)
{
    internal static NoteWire From(NoteSnapshot snapshot) => new(snapshot.Id, snapshot.Revision, snapshot.Name.Value);
}
