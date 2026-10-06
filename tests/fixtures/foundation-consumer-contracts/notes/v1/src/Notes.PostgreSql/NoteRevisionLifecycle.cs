using Microsoft.EntityFrameworkCore;
using Notes.Core;
using Orbyss.Foundation.Execution.Core;
using Orbyss.Foundation.PostgreSql;

namespace Notes.PostgreSql;

internal sealed class NoteRevisionLifecycle(IPostgreSqlUnitLeaseFactory<NotesDbContext> units,
    IExecutionDeadlineFactory deadlines, NoteOperationBudget budget) : INoteRevisionLifecycle
{
    public Task<NoteOutcome<NoteAcknowledgement>> CreateAsync(NoteOwner owner, Guid operationId, Guid noteId,
        NoteName name, CancellationToken cancellationToken) =>
        ExecuteAsync(owner, operationId, noteId, 0, name, cancellationToken);

    public Task<NoteOutcome<NoteAcknowledgement>> RenameAsync(NoteOwner owner, Guid operationId, Guid noteId,
        long expectedRevision, NoteName name, CancellationToken cancellationToken) =>
        ExecuteAsync(owner, operationId, noteId, expectedRevision, name, cancellationToken);

    private async Task<NoteOutcome<NoteAcknowledgement>> ExecuteAsync(NoteOwner owner, Guid operationId,
        Guid noteId, long expectedRevision, NoteName name, CancellationToken caller)
    {
        var digest = NoteOperationDigest.Create(expectedRevision == 0 ? NoteProtocol.Create : NoteProtocol.Rename,
            noteId, expectedRevision, name);
        using var outer = deadlines.Create(budget.Duration, caller);
        var commitStarted = false;
        try
        {
            await using var unit = await units.BeginUnitAsync(caller, outer);
            await using var db = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
            var token = unit.Deadline.Token;
            await using var transaction = await db.Database.BeginTransactionAsync(token);
            var previous = await db.Receipts.AsNoTracking().SingleOrDefaultAsync(row => row.Issuer == owner.Issuer
                && row.Subject == owner.Subject && row.OperationId == operationId, token);
            if (previous is not null) return Receipt(previous, digest);
            long revision;
            if (expectedRevision == 0)
            {
                if (await db.Notes.AnyAsync(row => row.Issuer == owner.Issuer && row.Subject == owner.Subject
                    && row.Id == noteId, token))
                {
                    var raced = await db.Receipts.AsNoTracking().SingleOrDefaultAsync(row => row.Issuer == owner.Issuer
                        && row.Subject == owner.Subject && row.OperationId == operationId, token);
                    return raced is null ? NoteOutcome<NoteAcknowledgement>.Denied(NoteFailure.NoteConflict) : Receipt(raced, digest);
                }
                revision = 1;
                db.Notes.Add(new() { Issuer = owner.Issuer, Subject = owner.Subject, Id = noteId, Revision = revision, Name = name.Value });
            }
            else
            {
                revision = checked(expectedRevision + 1);
                var updated = await db.Notes.Where(row => row.Issuer == owner.Issuer && row.Subject == owner.Subject
                    && row.Id == noteId && row.Revision == expectedRevision)
                    .ExecuteUpdateAsync(setters => setters.SetProperty(row => row.Revision, revision)
                        .SetProperty(row => row.Name, name.Value), token);
                if (updated == 0)
                {
                    var raced = await db.Receipts.AsNoTracking().SingleOrDefaultAsync(row => row.Issuer == owner.Issuer
                        && row.Subject == owner.Subject && row.OperationId == operationId, token);
                    if (raced is not null) return Receipt(raced, digest);
                    var exists = await db.Notes.AnyAsync(row => row.Issuer == owner.Issuer && row.Subject == owner.Subject
                        && row.Id == noteId, token);
                    return NoteOutcome<NoteAcknowledgement>.Denied(exists ? NoteFailure.RevisionConflict : NoteFailure.NotFound);
                }
            }
            db.Revisions.Add(new() { Issuer = owner.Issuer, Subject = owner.Subject, Id = noteId, Revision = revision, Name = name.Value });
            db.Receipts.Add(new() { Issuer = owner.Issuer, Subject = owner.Subject, OperationId = operationId,
                Digest = digest, Id = noteId, Revision = revision, Name = name.Value });
            await db.SaveChangesAsync(token);
            commitStarted = true;
            await transaction.CommitAsync(token);
            return NoteOutcome<NoteAcknowledgement>.Success(new(operationId, new(noteId, revision, name)));
        }
        catch (Exception exception) when (StorageFailure.IsExpected(exception))
        {
            // Reconciliation uses a fresh tracked unit/context and the SAME caller-owned deadline.
            var replay = await ReconcileAsync(owner, operationId, digest, caller, outer);
            if (replay is not null) return replay;
            if (commitStarted) return NoteOutcome<NoteAcknowledgement>.Denied(NoteFailure.Uncertain);
            _ = PostgreSqlFailureInfo.TryRead(exception, out var failure);
            return NoteOutcome<NoteAcknowledgement>.Denied(failure?.SqlState == StorageNames.UniqueViolation
                ? failure.ConstraintName switch
                {
                    StorageNames.ReceiptKey => NoteFailure.OperationConflict,
                    StorageNames.NoteKey => NoteFailure.NoteConflict,
                    StorageNames.RevisionKey => NoteFailure.RevisionConflict,
                    _ => NoteFailure.Unavailable
                } : NoteFailure.Unavailable);
        }
        catch (OperationCanceledException) when (commitStarted)
        {
            // Cancellation after commit begins does not prove rollback.
            var replay = await ReconcileAsync(owner, operationId, digest, caller, outer);
            return replay ?? NoteOutcome<NoteAcknowledgement>.Denied(NoteFailure.Uncertain);
        }
        catch (OperationCanceledException) when (!caller.IsCancellationRequested)
        {
            return NoteOutcome<NoteAcknowledgement>.Denied(NoteFailure.Unavailable);
        }
    }

    private async Task<NoteOutcome<NoteAcknowledgement>?> ReconcileAsync(NoteOwner owner, Guid operationId,
        string digest, CancellationToken caller, IExecutionDeadline outer)
    {
        try
        {
            await using var reconciliation = await units.BeginUnitAsync(caller, outer);
            await using var db = await reconciliation.Factory.CreateDbContextAsync(reconciliation.Deadline.Token);
            var receipt = await db.Receipts.AsNoTracking().SingleOrDefaultAsync(row => row.Issuer == owner.Issuer
                && row.Subject == owner.Subject && row.OperationId == operationId, reconciliation.Deadline.Token);
            return receipt is null ? null : Receipt(receipt, digest);
        }
        catch (OperationCanceledException) { return null; }
        catch (Exception exception) when (StorageFailure.IsExpected(exception)) { return null; }
    }

    private static NoteOutcome<NoteAcknowledgement> Receipt(ReceiptRow receipt, string digest)
    {
        if (!string.Equals(receipt.Digest, digest, StringComparison.Ordinal))
            return NoteOutcome<NoteAcknowledgement>.Denied(NoteFailure.OperationConflict);
        return NoteOutcome<NoteAcknowledgement>.Success(new(receipt.OperationId, new(receipt.Id, receipt.Revision, NoteName.Create(receipt.Name))));
    }
}
