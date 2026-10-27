using CShells.DependencyInjection;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using ProgramKit.Examples.CShellsInitializerOwnership;

internal sealed class ProbeHost : IAsyncDisposable
{
    private readonly ServiceProvider provider;

    private ProbeHost(ServiceProvider provider)
    {
        this.provider = provider;
        Registry = provider.GetRequiredService<IShellRegistry>();
    }

    public IShellRegistry Registry { get; } = null!;

    public static ProbeHost Create<TFeature>(SyntheticResourceObservation observation, TestObservation? other = null)
        where TFeature : class, IShellFeature
    {
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddSingleton<IConfiguration>(new ConfigurationBuilder().Build());
        services.AddSingleton(observation);
        services.AddSingleton(other ?? new TestObservation());
        services.AddCShells(builder => builder.WithAssemblyContaining<ResourceFeature>()
            .AddShell("probe", shell => shell.WithFeature<TFeature>()));
        return new ProbeHost(services.BuildServiceProvider());
    }

    public async Task DisposeGenerationAsync(IShell shell)
    {
        if (shell.State == ShellLifecycleState.Disposed)
            return;
        var operation = await Registry.DrainAsync(shell);
        await operation.WaitAsync().WaitAsync(TimeSpan.FromSeconds(10));
        var deadline = DateTime.UtcNow.AddSeconds(10);
        while (shell.State != ShellLifecycleState.Disposed && DateTime.UtcNow < deadline)
            await Task.Delay(5);
        Program.Require(shell.State == ShellLifecycleState.Disposed, "Actual generation teardown was not observed");
    }

    public async ValueTask DisposeAsync()
    {
        try
        {
            foreach (var shell in Registry.GetAll("probe").ToArray())
                await DisposeGenerationAsync(shell);
        }
        finally
        {
            await provider.DisposeAsync();
        }
    }
}
