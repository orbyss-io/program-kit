using CShells.DependencyInjection;
using CShells.Lifecycle;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

namespace ProgramKit.Examples.TypedOperation.OptionsProbe;

/// <summary>Proves actual shell activation observes the shipped bound API options before later work.</summary>
internal static class Program
{
    /// <summary>Exercises absent, null, empty, oversized and valid configured values.</summary>
    private static async Task Main()
    {
        await VerifyCaseAsync(
            name: "missing",
            supply: false,
            prefix: null,
            accepted: false
        );
        await VerifyCaseAsync(
            name: "null",
            supply: true,
            prefix: null,
            accepted: false
        );
        await VerifyCaseAsync(
            name: "empty",
            supply: true,
            prefix: "",
            accepted: false
        );
        var oversized = new string('x', 33);
        await VerifyCaseAsync(
            name: "oversized",
            supply: true,
            prefix: oversized,
            accepted: false
        );
        await VerifyCaseAsync(
            name: "configured",
            supply: true,
            prefix: "nondefault-",
            accepted: true
        );

        Console.WriteLine("ACTUAL_NATIVE_API_OPTIONS_ACTIVATION_PASSED: missing, null, empty, oversized, configured; later effects remain ordered.");
    }

    /// <summary>Uses native registry activation, including failed-generation exclusion and actual configured values.</summary>
    private static async Task VerifyCaseAsync(
        string name,
        bool supply,
        string? prefix,
        bool accepted
    )
    {
        const string path = "CShells:Shells:probe";
        var values = new Dictionary<string, string?> { [path + ":Features:TypedLabelOptionsProbe"] = "true" };
        if (supply)
            values[path + ":Configuration:Sample:Api:Prefix"] = prefix;
        var configurationBuilder = new ConfigurationBuilder();
        var configuration = configurationBuilder
            .AddInMemoryCollection(values)
            .Build();
        var observation = new EffectObservation();
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddSingleton<IConfiguration>(configuration);
        services.AddSingleton(observation);

        void ConfigureShells(CShellsBuilder shells)
        {
            shells
                .WithAssemblyContaining<OptionsFeature>()
                .WithConfigurationProvider(configuration);
        }

        services.AddCShells(ConfigureShells);
        await using var provider = services.BuildServiceProvider();
        var registry = provider.GetRequiredService<IShellRegistry>();
        IShell? shell = null;
        try
        {
            shell = await registry.GetOrActivateAsync("probe");
            if (!accepted)
                throw new InvalidOperationException("Invalid API options activated: " + name);
        }
        catch (OptionsValidationException error) when (error.OptionsType == typeof(LabelApiOptions))
        {
            if (accepted)
                throw;
        }

        if (accepted)
        {
            if (shell is null || shell.State != ShellLifecycleState.Active || observation.Starts != 1)
                throw new InvalidOperationException("Valid API options did not reach the native later effect phase.");
            var options = shell.ServiceProvider.GetRequiredService<IOptions<LabelApiOptions>>();
            if (options.Value.Prefix != prefix)
                throw new InvalidOperationException("Native binding lost the nondefault API prefix.");
            var draining = await registry.DrainAsync(shell);
            await draining.WaitAsync();
        }
        else
        {
            var active = registry.GetActive("probe");
            var generations = registry.GetAll("probe");
            if (active is not null || generations.Count != 0 || observation.Starts != 0)
                throw new InvalidOperationException("Invalid API options published a generation or performed later protected work.");
        }
    }
}
