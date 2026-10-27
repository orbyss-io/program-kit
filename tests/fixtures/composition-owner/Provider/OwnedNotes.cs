using System.Linq.Expressions;
using System.Security.Cryptography;
using Application.Core;
using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace Application.PostgreSql;

/// <summary>Owns actual independently disposed native units and exact owner-qualified database effects.</summary>
internal sealed class OwnedNotes(IPostgreSqlUnitLeaseFactory<PolicyDbContext> units, OwnedNoteSecret secret) : IOwnedNotes
{
    /// <inheritdoc />
    public async Task<Guid> CreateAsync(OwnedActor actor, CancellationToken cancellationToken)
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        var id = Guid.NewGuid();
        const string value = "synthetic-owner-note";
        var digest = secret.Sign(
            actor.Issuer,
            actor.Subject,
            id,
            value
        );
        var row = new OwnedNoteRow { Id = id, OwnerIssuer = actor.Issuer, OwnerSubject = actor.Subject, Value = value, Digest = digest };
        context.Add(row);
        await context.SaveChangesAsync(unit.Deadline.Token);
        return id;
    }
    /// <inheritdoc />
    public async Task<string?> ReadAsync(
        OwnedActor actor,
        Guid id,
        CancellationToken cancellationToken
    )
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        Expression<Func<OwnedNoteRow, bool>> owned = note => note.Id == id && note.OwnerIssuer == actor.Issuer && note.OwnerSubject == actor.Subject;
        var query = context
            .Set<OwnedNoteRow>()
            .AsNoTracking();
        var note = await query.SingleOrDefaultAsync(owned, unit.Deadline.Token);
        if (note is null) return null;
        var expected = secret.Sign(
            note.OwnerIssuer,
            note.OwnerSubject,
            note.Id,
            note.Value
        );
        if (!CryptographicOperations.FixedTimeEquals(expected, note.Digest)) throw new InvalidOperationException("OWNER_NOTE_INTEGRITY");
        return note.Value;
    }
}
