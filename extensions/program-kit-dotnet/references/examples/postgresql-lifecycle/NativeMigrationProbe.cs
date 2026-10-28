using CShells.DependencyInjection;
using CShells.Lifecycle;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Npgsql;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Exercises read-only migration admission and an ordinary EF write under the runtime identity.</summary>
public static class NativeMigrationProbe
{
    /// <summary>Uses real shell/unit/context lifetimes; never changes the schema or migration history.</summary>
    public static async Task RunAsync(string operation)
    {
        if (Environment.GetEnvironmentVariable("PK_FIXTURE_EF_DEPLOYMENT") is not null
            || Environment.GetEnvironmentVariable("PK_FIXTURE_DEPLOYMENT") is not null)
            throw new InvalidOperationException("Deployment credentials must not enter the runtime child.");
        var connection = new NpgsqlConnectionStringBuilder(Environment.GetEnvironmentVariable("PK_FIXTURE_RUNTIME"))
            { SearchPath = "ef_example" };
        var values = new Dictionary<string, string?>
        {
            ["CShells:Shells:native-ef:Features:ProgramKit.NativeEfMigrations"] = "true",
            ["CShells:Shells:native-ef:Configuration:Foundation:PostgreSql:Policies:fixture:ConnectionString"] = connection.ConnectionString
        };
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(values).Build();
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddSingleton<IConfiguration>(configuration);
        services.AddCShells(shells => shells.WithConfigurationProvider(configuration));
        await using var provider = services.BuildServiceProvider();
        var shell = await provider.GetRequiredService<IShellRegistry>().GetOrActivateAsync("native-ef");
        var leases = shell.ServiceProvider.GetRequiredService<IPostgreSqlUnitLeaseFactory<NativeMigrationContext>>();
        await using var unit = await leases.BeginUnitAsync();
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        context.Add(new NativeMigrationEntry { Value = operation });
        await context.SaveChangesAsync(unit.Deadline.Token);
        Console.WriteLine("native-ef-runtime-admitted");
    }
}
