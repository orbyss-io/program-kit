using Microsoft.EntityFrameworkCore;
using Notes.Core;
using Orbyss.Foundation.PostgreSql;

namespace Notes.PostgreSql;

internal sealed class NoteQueries(IPostgreSqlUnitLeaseFactory<NotesDbContext> units) : INoteQueries
{
    public async Task<NoteOutcome<NoteSnapshot>> ReadAsync(NoteOwner owner, Guid noteId, CancellationToken cancellationToken)
    {
        try
        {
            await using var unit = await units.BeginUnitAsync(cancellationToken);
            await using var db = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
            var row = await db.Notes.AsNoTracking().SingleOrDefaultAsync(row => row.Issuer == owner.Issuer
                && row.Subject == owner.Subject && row.Id == noteId, unit.Deadline.Token);
            return row is null ? NoteOutcome<NoteSnapshot>.Denied(NoteFailure.NotFound)
                : NoteOutcome<NoteSnapshot>.Success(Snapshot(row));
        }
        catch (Exception exception) when (StorageFailure.IsExpected(exception))
        { return NoteOutcome<NoteSnapshot>.Denied(NoteFailure.Unavailable); }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        { return NoteOutcome<NoteSnapshot>.Denied(NoteFailure.Unavailable); }
    }

    public async Task<NoteOutcome<NotePage>> ListAsync(NoteOwner owner, Guid? afterNoteId, int size, CancellationToken cancellationToken)
    {
        try
        {
            await using var unit = await units.BeginUnitAsync(cancellationToken);
            await using var db = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
            var query = db.Notes.AsNoTracking().Where(row => row.Issuer == owner.Issuer && row.Subject == owner.Subject);
            if (afterNoteId is { } after) query = query.Where(row => row.Id.CompareTo(after) > 0);
            var rows = await query.OrderBy(row => row.Id).Take(checked(size + 1)).ToListAsync(unit.Deadline.Token);
            var items = rows.Take(size).Select(Snapshot).ToArray();
            return NoteOutcome<NotePage>.Success(new(items, rows.Count > size ? items[^1].Id : null));
        }
        catch (Exception exception) when (StorageFailure.IsExpected(exception))
        { return NoteOutcome<NotePage>.Denied(NoteFailure.Unavailable); }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        { return NoteOutcome<NotePage>.Denied(NoteFailure.Unavailable); }
    }

    private static NoteSnapshot Snapshot(NoteRow row)
    {
        return new(row.Id, row.Revision, NoteName.Create(row.Name));
    }
}
