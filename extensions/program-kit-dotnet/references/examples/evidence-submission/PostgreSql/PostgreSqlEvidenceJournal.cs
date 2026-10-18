using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Storage;
using Orbyss.Foundation.Json;

namespace ProgramKit.Examples.Evidence;

/// <summary>Owns immutable preparation, conditional acceptance and owner-filtered observation.</summary>
public sealed class PostgreSqlEvidenceJournal(EvidenceDbContext database) : IEvidenceJournal
{
    /// <summary>Finite native admission for the provider's private JSON snapshot.</summary>
    private static readonly JsonProfile Profile = CreateProfile();

    /// <summary>Admits and retains one immutable owned preparation.</summary>
    public async Task<EvidenceReceipt> PrepareAsync(
        string owner,
        EvidencePacket packet,
        CancellationToken cancellation
    )
    {
        var identifier = Guid.NewGuid();
        var identity = identifier.ToString("N");
        var content = packet.CopyContent();
        var document = new StoredPacket(
            packet.Title,
            packet.Date,
            packet.Hash,
            content
        );
        var bytes = Profile.Serialize(document);
        var json = System.Text.Encoding.UTF8.GetString(bytes);
        var row = new EvidenceRow { Id = identity, Owner = owner, Packet = json };
        database.Entries.Add(row);
        await database.SaveChangesAsync(cancellation);
        return Receipt(row);
    }

    /// <summary>Accepts the retained owned identity without repeating its established effect.</summary>
    public async Task<EvidenceReceipt?> AcceptAsync(
        string owner,
        string identity,
        CancellationToken cancellation
    )
    {
        var entity = database.Model.FindEntityType(typeof(EvidenceRow))!;
        var tableName = entity.GetTableName()!;
        var schema = entity.GetSchema();
        var store = StoreObjectIdentifier.Table(tableName, schema);
        var quotes = database.GetService<ISqlGenerationHelper>();
        var table = quotes.DelimitIdentifier(tableName, schema);
        string Column(string property)
        {
            var mapped = entity.FindProperty(property)!;
            var name = mapped.GetColumnName(store)!;
            return quotes.DelimitIdentifier(name);
        }
        var id = Column("Id");
        var ownerColumn = Column("Owner");
        var accepted = Column("Accepted");
        var revision = Column("Revision");
        // Closed reviewed structure, provider-quoted mapped identifiers and separately bound values.
        // The independent accepted-schema test must reject mapping drift before deployment.
        var sql = $"UPDATE {table} SET {accepted}=TRUE, {revision}={revision}+1 WHERE {id}={{0}} AND {ownerColumn}={{1}} AND NOT {accepted}";
        object[] parameters = [identity, owner];
        await database.Database.ExecuteSqlRawAsync(
            sql,
            parameters,
            cancellation
        );
        return await FindAsync(
            owner,
            identity,
            cancellation
        );
    }

    /// <summary>Observes the existing owned submission without a new business effect.</summary>
    public async Task<EvidenceReceipt?> FindAsync(
        string owner,
        string identity,
        CancellationToken cancellation
    )
    {
        var row = await database.Entries
            .AsNoTracking()
            .SingleOrDefaultAsync(entry => entry.Id == identity && entry.Owner == owner, cancellation);
        return row is null ? null : Receipt(row);
    }

    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private static EvidenceReceipt Receipt(EvidenceRow row)
    {
        var bytes = System.Text.Encoding.UTF8.GetBytes(row.Packet);
        var packet = Profile.Deserialize<StoredPacket>(bytes);
        return new EvidenceReceipt(
            row.Id,
            packet.Title,
            packet.Date,
            packet.Hash,
            row.Accepted
        );
    }
    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private static JsonProfile CreateProfile()
    {
        var settings = new JsonProfileSettings { MaxBytes = 32768 };
        return new JsonProfile(settings);
    }

}
