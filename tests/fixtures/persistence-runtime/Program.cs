// Non-shipping integration fixture. Production admission/HTTP behavior stays consumer-owned.
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using System.Xml.Linq;

var suite = new XElement("testsuite");
var failed = false;
async Task Case(string name, Func<Task> body)
{
    var test = new XElement("testcase", new XAttribute("classname", "PostgreSql"), new XAttribute("name", name));
    try { await body().WaitAsync(TimeSpan.FromSeconds(25)); }
    catch (Exception error) { failed = true; test.Add(new XElement("failure", error.ToString())); }
    suite.Add(test);
}
if (args[0] == "exercise")
{
    await Case("explicit_reviewable_migrations", async () =>
    {
        await using var store = new Store();
        var script = store.GetService<IMigrator>().GenerateScript(options: MigrationsSqlGenerationOptions.Idempotent);
        Check(script.Contains("CREATE TABLE", StringComparison.Ordinal) && script.Contains("__EFMigrationsHistory", StringComparison.Ordinal), "missing reviewed migration artifact");
        await store.Database.MigrateAsync(); // Explicit test deployment action, never host startup.
        Check(!(await store.Database.GetPendingMigrationsAsync()).Any() && !store.Database.HasPendingModelChanges(), "migration/model drift");
        store.Stock.Add(new Stock { Id = "camera", Available = 2, Version = 1 }); await store.SaveChangesAsync();
    });
    await Case("transaction_rollback_is_atomic", async () =>
    {
        await using var strategyOwner = new Store();
        await strategyOwner.Database.CreateExecutionStrategy().ExecuteAsync(async () =>
        {
            await using var store = new Store();
            await using var transaction = await store.Database.BeginTransactionAsync();
            store.Operations.Add(new Operation { Id = "rolled-back", Payload = "camera", Result = "never", Tenant = "A" });
            await store.SaveChangesAsync(); await transaction.RollbackAsync();
        });
        await using var verify = new Store();
        Check(!await verify.Operations.AnyAsync(o => o.Id == "rolled-back"), "rollback retained effects");
    });
    await Case("real_provider_optimistic_contention", async () =>
    {
        await using var first = new Store(); await using var second = new Store();
        var a = await first.Stock.SingleAsync(); var b = await second.Stock.SingleAsync();
        a.Available--; a.Version++; b.Available--; b.Version++;
        await first.SaveChangesAsync();
        try { await second.SaveChangesAsync(); throw new InvalidOperationException("stale write admitted"); }
        catch (DbUpdateConcurrencyException) { }
        await using var verify = new Store(); Check((await verify.Stock.SingleAsync()).Available == 1, "contention lost inventory");
    });
    await Case("stable_replay_and_conflicting_identity", async () =>
    {
        var first = await Reserve("accepted", "camera", loseAcknowledgement: true); var again = await Reserve("accepted", "camera");
        Check(first == again, "replay identity changed");
        try { await Reserve("accepted", "different"); throw new Exception("conflicting identity admitted"); }
        catch (ArgumentException) { }
        await using var verify = new Store();
        Check(await verify.Operations.CountAsync() == 1 && (await verify.Stock.SingleAsync()).Available == 0, "replay or conflict repeated effects");
    });
    await Case("lost_commit_acknowledgement_is_verified_before_replay", async () =>
    {
        Check(Policies.LostAcknowledgements == 1 && Policies.VerifiedReplayAfterLoss,
              "fixture did not replay a committed transaction through the actual provider execution strategy");
        Check(await Reserve("accepted", "camera") == "reservation-accepted", "stable identity did not resolve ambiguous outcome");
        await using var verify = new Store(); Check(await verify.Operations.CountAsync() == 1, "ambiguous replay duplicated operation");
    });
    await Case("provider_translation_and_tenant_predicate", async () =>
    {
        await using var store = new Store();
        Check(await store.Operations.AsNoTracking().Where(o => o.Tenant == "B").CountAsync() == 0, "tenant predicate bypassed");
        Check((await store.Operations.AsNoTracking().Where(o => o.Tenant == "A").Select(o => o.Result).ToArrayAsync()).Length == 1, "owned projection failed");
        try { _ = await store.Operations.Where(o => Policies.LocalPolicy(o.Payload)).ToArrayAsync(); throw new Exception("untranslatable predicate accepted"); }
        catch (InvalidOperationException) { }
    });
}
else if (args[0] == "restart")
{
    await Case("database_restart_preserves_admission_and_outbox", async () =>
    {
        await using var store = new Store(); var operation = await store.Operations.SingleAsync();
        Check(operation.Id == "accepted" && operation.Result == "reservation-accepted" && operation.PendingNotification, "restart lost durable operation/effect ownership");
        Check((await store.Stock.SingleAsync()).Available == 0, "restart restored consumed capacity");
    });
    await Case("failed_notification_retains_durable_retry_owner", async () =>
    {
        await using var store = new Store(); var operation = await store.Operations.SingleAsync();
        try { throw new IOException("receiver unavailable before acknowledgement"); }
        catch (IOException) { Check(operation.PendingNotification, "failure erased durable retry owner"); }
        operation.PendingNotification = false; operation.Deliveries++; await store.SaveChangesAsync();
        await using var replay = new Store(); var retained = await replay.Operations.SingleAsync();
        if (retained.PendingNotification) retained.Deliveries++;
        Check(retained.Deliveries == 1, "completed retry repeated acknowledged effect");
    });
}
else throw new ArgumentException("unknown fixture phase");
new XDocument(suite).Save(args[1]);
return failed ? 1 : 0;

static void Check(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
static async Task<string> Reserve(string identity, string payload, bool loseAcknowledgement = false)
{
    await using var strategyOwner = new Store();
    return await strategyOwner.Database.CreateExecutionStrategy().ExecuteAsync(async () =>
    {
        await using var store = new Store(); // Each replay starts from newly observed durable state.
        await using var transaction = await store.Database.BeginTransactionAsync();
        var existing = await store.Operations.SingleOrDefaultAsync(o => o.Id == identity);
        if (existing is not null)
        {
            if (existing.Payload != payload) throw new ArgumentException("conflicting replay identity");
            if (loseAcknowledgement) Policies.VerifiedReplayAfterLoss = true;
            return existing.Result;
        }
        var stock = await store.Stock.SingleAsync();
        if (stock.Available <= 0) throw new InvalidOperationException("capacity denied");
        stock.Available--; stock.Version++;
        var operation = new Operation { Id = identity, Payload = payload, Result = "reservation-" + identity, Tenant = "A", PendingNotification = true };
        store.Operations.Add(operation); await store.SaveChangesAsync(); await transaction.CommitAsync();
        if (loseAcknowledgement && Policies.LostAcknowledgements++ == 0)
        {
            // Deterministic injection after a real commit, at the driver's transient-failure boundary.
            var lost = new Npgsql.NpgsqlException("injected lost acknowledgement", new TimeoutException());
            Check(lost.IsTransient, "injection does not exercise the provider retry classifier");
            throw lost;
        }
        return operation.Result;
    });
}

public sealed class Store : DbContext
{
    public DbSet<Operation> Operations => Set<Operation>();
    public DbSet<Stock> Stock => Set<Stock>();
    protected override void OnConfiguring(DbContextOptionsBuilder options) => options.UseNpgsql(
        Environment.GetEnvironmentVariable("LENDING_FIXTURE_CONNECTION_STRING") ?? "Host=127.0.0.1;Database=fixture-design-only",
        provider => provider.EnableRetryOnFailure(2));
    protected override void OnModelCreating(ModelBuilder model)
    {
        model.Entity<Operation>().HasKey(o => o.Id);
        model.Entity<Operation>().HasIndex(o => new { o.Tenant, o.Id });
        model.Entity<Stock>().HasKey(s => s.Id);
        model.Entity<Stock>().Property(s => s.Version).IsConcurrencyToken();
    }
}
public sealed class Operation
{
    public string Id { get; set; } = "";
    public string Payload { get; set; } = "";
    public string Result { get; set; } = "";
    public string Tenant { get; set; } = "";
    public bool PendingNotification { get; set; }
    public int Deliveries { get; set; }
}
public sealed class Stock
{
    public string Id { get; set; } = "";
    public int Available { get; set; }
    public int Version { get; set; }
}
public static class Policies
{
    public static int LostAcknowledgements;
    public static bool VerifiedReplayAfterLoss;
    public static bool LocalPolicy(string payload) => payload.StartsWith("camera", StringComparison.Ordinal);
}
