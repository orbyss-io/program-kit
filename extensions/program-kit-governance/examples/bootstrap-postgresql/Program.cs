// Synthetic mechanism proof, not a consumer schema or migration policy.
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using System.Xml.Linq;

var suite = new XElement("testsuite");
var failed = false;
async Task Case(string name, Func<Task> test)
{
    var result = new XElement("testcase", new XAttribute("classname", "PostgreSql"), new XAttribute("name", name));
    try { await test().WaitAsync(TimeSpan.FromSeconds(30)); }
    catch (Exception error) { failed = true; result.Add(new XElement("failure", error.ToString())); }
    suite.Add(result);
}
if (args[0] == "exercise")
{
    await Case("write_read", async () =>
    {
        await using var db = new Store();
        await db.Database.EnsureCreatedAsync(); // Only this disposable synthetic database.
        db.Rows.Add(new Row { Id = "item", Value = "initial", Revision = 1 });
        await db.SaveChangesAsync();
        await using var verify = new Store();
        Check((await verify.Rows.AsNoTracking().SingleAsync()).Value == "initial", "write/read failed");
    });
    await Case("atomic_expected_revision_conflict", async () =>
    {
        await using var first = new Store();
        await using var stale = new Store();
        var current = await first.Rows.SingleAsync();
        var old = await stale.Rows.SingleAsync();
        current.Value = "winner"; current.Revision++;
        old.Value = "loser"; old.Revision++;
        await first.SaveChangesAsync();
        await using var transaction = await stale.Database.BeginTransactionAsync();
        stale.Rows.Add(new Row { Id = "must-rollback", Value = "side effect", Revision = 1 });
        var rejected = false;
        try { await stale.SaveChangesAsync(); }
        catch (DbUpdateConcurrencyException) { rejected = true; }
        await transaction.RollbackAsync();
        Check(rejected, "stale update was accepted");
        await using var verify = new Store();
        var retained = await verify.Rows.AsNoTracking().SingleAsync();
        Check(retained.Value == "winner" && retained.Revision == 2, "conflict changed committed state");
    });
    await Case("transaction_rollback", async () =>
    {
        await using var db = new Store();
        await using var transaction = await db.Database.BeginTransactionAsync();
        db.Rows.Add(new Row { Id = "rolled-back", Revision = 1 });
        await db.SaveChangesAsync(); await transaction.RollbackAsync();
        await using var verify = new Store();
        Check(await verify.Rows.CountAsync() == 1, "rollback retained a write");
    });
    await Case("expected_lock_error_classification", () =>
    {
        var expected = new Npgsql.PostgresException("lock timeout", "ERROR", "ERROR", "55P03");
        var unrelated = new Npgsql.PostgresException("unique violation", "ERROR", "ERROR", "23505");
        Check(IsExpectedLockTimeout(expected), "direct lock timeout was not recognized");
        Check(IsExpectedLockTimeout(new InvalidOperationException("EF wrapper", expected)), "EF-wrapped lock timeout was not recognized");
        Check(!IsExpectedLockTimeout(unrelated), "unrelated PostgreSQL error was accepted");
        Check(!IsExpectedLockTimeout(new InvalidOperationException("EF wrapper", unrelated)), "wrapped unrelated error was accepted");
        Check(!IsExpectedLockTimeout(new InvalidOperationException("unrelated failure")), "bare InvalidOperationException was accepted");
        Check(!IsExpectedLockTimeout(new TimeoutException("connection timeout")), "non-PostgreSQL timeout was accepted");
        return Task.CompletedTask;
    });
    await Case("row_lock_exclusion_and_release", async () =>
    {
        await using var holder = new Store();
        await using var contender = new Store();
        holder.Database.SetCommandTimeout(5);
        contender.Database.SetCommandTimeout(5);
        await using var held = await holder.Database.BeginTransactionAsync(System.Data.IsolationLevel.ReadCommitted);
        var rows = await holder.Rows.FromSqlRaw("""SELECT * FROM "Rows" WHERE "Id" = 'item' FOR UPDATE""").ToListAsync();
        Check(rows.Count == 1, "lock target missing");
        rows[0].Value = "uncommitted-lock-holder";
        await holder.SaveChangesAsync();
        await using (var blocked = await contender.Database.BeginTransactionAsync(System.Data.IsolationLevel.ReadCommitted))
        {
            await contender.Database.ExecuteSqlRawAsync("SET LOCAL lock_timeout = '250ms'");
            var denied = false;
            try
            {
                await contender.Rows.FromSqlRaw("""SELECT * FROM "Rows" WHERE "Id" = 'item' FOR UPDATE""").AsNoTracking().ToListAsync();
            }
            catch (Exception error) when (IsExpectedLockTimeout(error)) { denied = true; }
            await blocked.RollbackAsync();
            Check(denied, "competing transaction acquired the held row lock");
        }
        await held.RollbackAsync();
        await using var successor = new Store();
        successor.Database.SetCommandTimeout(5);
        await using var acquired = await successor.Database.BeginTransactionAsync(System.Data.IsolationLevel.ReadCommitted);
        await successor.Database.ExecuteSqlRawAsync("SET LOCAL lock_timeout = '2s'");
        var retained = await successor.Rows.FromSqlRaw("""SELECT * FROM "Rows" WHERE "Id" = 'item' FOR UPDATE""").AsNoTracking().ToListAsync();
        Check(retained.Count == 1 && retained[0].Value == "winner" && retained[0].Revision == 2,
            "rollback did not release the lock and preserve committed data");
        await acquired.CommitAsync();
    });
}
else if (args[0] == "restart")
{
    await Case("restart_preserves_state", async () =>
    {
        await using var db = new Store();
        var row = await db.Rows.AsNoTracking().SingleAsync();
        Check(row.Id == "item" && row.Value == "winner" && row.Revision == 2, "restart lost committed state");
    });
}
else throw new ArgumentException("Unknown probe phase");
new XDocument(suite).Save(args[1]);
return failed ? 1 : 0;

// EF's default Npgsql execution strategy wraps transient PostgreSQL errors.
// Accept only the expected SQLSTATE at this specific contended-lock query.
static bool IsExpectedLockTimeout(Exception error) => error is
    Npgsql.PostgresException { SqlState: Npgsql.PostgresErrorCodes.LockNotAvailable } or
    InvalidOperationException { InnerException: Npgsql.PostgresException { SqlState: Npgsql.PostgresErrorCodes.LockNotAvailable } };

static void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
sealed class Row
{
    public required string Id { get; set; }
    public string Value { get; set; } = "";
    public int Revision { get; set; }
}
sealed class RowConfiguration : IEntityTypeConfiguration<Row>
{
    public void Configure(EntityTypeBuilder<Row> row)
    {
        row.HasKey(x => x.Id);
        row.Property(x => x.Revision).IsConcurrencyToken();
    }
}
sealed class Store : DbContext
{
    public DbSet<Row> Rows => Set<Row>();
    protected override void OnConfiguring(DbContextOptionsBuilder options) => options.UseNpgsql(
        Environment.GetEnvironmentVariable("PROGRAM_KIT_PROBE_CONNECTION") ?? throw new InvalidOperationException("Missing isolated database connection"));
    protected override void OnModelCreating(ModelBuilder builder) => builder.ApplyConfiguration(new RowConfiguration());
}
