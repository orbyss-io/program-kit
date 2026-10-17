using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CShells.DependencyInjection;
using CShells.Lifecycle;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Exercises real native shell discovery and provider registration from emitted input.</summary>
public static class PrivateFilesProbe
{
    /// <summary>Reports only the configured root hash, never the root or another configuration value.</summary>
    public static async Task RunAsync(string configurationPath)
    {
        var values = JsonSerializer.Deserialize<Dictionary<string, string?>>(await File.ReadAllTextAsync(configurationPath))
            ?? throw new InvalidOperationException("Missing emitted fixture configuration.");
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(values).Build();
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddSingleton<IConfiguration>(configuration);
        services.AddCShells(shells => shells.WithConfigurationProvider(configuration));
        await using var provider = services.BuildServiceProvider();
        var shell = await provider.GetRequiredService<IShellRegistry>().GetOrActivateAsync("fixture");
        var actual = shell.ServiceProvider.GetRequiredService<PrivateFilesOptions>();
        Console.WriteLine(Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(actual.Root))));
    }
}
