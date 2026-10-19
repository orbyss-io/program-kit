namespace SnapshotLesson;

/// <summary>Serves repeated report queries over one admitted immutable snapshot.</summary>
public sealed class OwnerReport
{
    /// <summary>Owns the selected snapshot-query implementation.</summary>
    private readonly SnapshotQuery query;

    /// <summary>Prepares this report from the caller-owned accepted snapshot.</summary>
    public OwnerReport(IEnumerable<Note> acceptedSnapshot)
    {
        query = new SnapshotQuery(acceptedSnapshot);
    }

    /// <summary>Returns rows only for the admitted exact owner.</summary>
    public IReadOnlyList<Note> Rows(string admittedOwner)
    {
        return query.ForOwner(admittedOwner);
    }
}
