using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Configuration;
using CShells.DependencyInjection;
using CShells.Lifecycle;
using Orbyss.Foundation.PostgreSql;
using Npgsql;
using ProgramKit.Examples.PostgreSql;

if (args is ["binding", var configurationPath])
{
    await PrivateFilesProbe.RunAsync(configurationPath);
    return;
}
if (args is ["ef-runtime", var operation])
{
    await NativeMigrationProbe.RunAsync(operation);
    return;
}
if (args.Length != 3 || args[0] is not ("prepare" or "runtime" or "cleanup"))
    throw new ArgumentException("Expected prepare|runtime|cleanup <fixture-id> <unique-operation-id>.");
var identity = new FixtureIdentity(args[1]);
if (args[0] != "runtime")
{
    Console.WriteLine(await FixtureDeployment.PrepareAsync(identity, args[0] == "cleanup"));
    return;
}
// Observe only the runtime connection. This process receives no deployment credential.
if (Environment.GetEnvironmentVariable("PK_FIXTURE_DEPLOYMENT") is not null)
    throw new InvalidOperationException("Deployment credentials must not enter a runtime child.");
await using var observed = await identity.OpenAsync(deployment: false);
var services = new ServiceCollection();
services.AddLogging();
var runtimeConnection = new NpgsqlConnectionStringBuilder(Environment.GetEnvironmentVariable("PK_FIXTURE_RUNTIME"))
    { SearchPath = identity.Schema, ApplicationName = "pk-runtime-" + identity.Id };
var values = new Dictionary<string, string?>
{
    ["CShells:Shells:fixture:Features:ProgramKit.PostgreSqlLifecycle"] = "true",
    ["CShells:Shells:fixture:Configuration:Foundation:PostgreSql:Policies:fixture:ConnectionString"] = runtimeConnection.ConnectionString,
    ["CShells:Shells:fixture:Configuration:Foundation:PostgreSql:Policies:fixture:OperationTimeout"] = "00:00:15",
    ["CShells:Shells:fixture:Configuration:Foundation:PostgreSql:Policies:fixture:ConnectionTimeout"] = "00:00:03",
    ["CShells:Shells:fixture:Configuration:Foundation:PostgreSql:Policies:fixture:CommandTimeout"] = "00:00:03",
    ["CShells:Shells:fixture:Configuration:Foundation:PostgreSql:Policies:fixture:LockTimeout"] = "00:00:01"
};
var configuration = new ConfigurationBuilder().AddInMemoryCollection(values).Build();
services.AddSingleton<IConfiguration>(configuration);
services.AddCShells(shells => shells.WithConfigurationProvider(configuration));
await using var provider = services.BuildServiceProvider();
var shell = await provider.GetRequiredService<IShellRegistry>().GetOrActivateAsync("fixture");
var leases = shell.ServiceProvider.GetRequiredService<IPostgreSqlUnitLeaseFactory<FixtureContext>>();
await using var unit = await leases.BeginUnitAsync();
await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
var admitted = await context.Database.SqlQueryRaw<int>("""
    SELECT CASE WHEN
      (SELECT count(*)=1 AND min(revision)=1 FROM journal)
      AND has_schema_privilege(current_user,current_schema(),'USAGE')
      AND NOT has_schema_privilege(current_user,current_schema(),'CREATE')
      AND has_table_privilege(current_user,'entries','SELECT')
      AND has_table_privilege(current_user,'entries','INSERT')
      AND has_table_privilege(current_user,'entries','UPDATE')
      AND has_table_privilege(current_user,'entries','DELETE')
      AND has_table_privilege(current_user,'journal','SELECT')
      AND NOT has_table_privilege(current_user,'journal','INSERT,UPDATE,DELETE')
      AND has_sequence_privilege(current_user,'entries_id_seq','USAGE')
      AND has_sequence_privilege(current_user,'entries_id_seq','SELECT')
      THEN 1 ELSE 0 END AS "Value"
    """).SingleAsync(unit.Deadline.Token);
if (admitted != 1) throw new InvalidOperationException("Required schema revision/runtime permissions are unavailable.");
await using var transaction = await context.Database.BeginTransactionAsync(unit.Deadline.Token);
await context.Database.ExecuteSqlRawAsync("INSERT INTO entries(value) VALUES ({0})", [args[2]], unit.Deadline.Token);
// Synthetic overlap window for independent server observation in the qualifier.
await context.Database.ExecuteSqlRawAsync("SELECT pg_sleep(1)", unit.Deadline.Token);
await transaction.CommitAsync(unit.Deadline.Token);
var count = await context.Database.SqlQueryRaw<int>("SELECT count(*)::int AS \"Value\" FROM entries").SingleAsync(unit.Deadline.Token);
if (count < 1) throw new InvalidOperationException("Committed runtime effect not visible.");
Console.WriteLine("runtime-admitted");
