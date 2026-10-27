using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;

internal sealed class TestObservation
{
    public List<TestLifetime> Lifetimes { get; } = [];
}

internal sealed class TestLifetime
{
    private int initializations;
    private int disposals;
    public int Initializations => Volatile.Read(ref initializations);
    public int Disposals => Volatile.Read(ref disposals);
    public void Initialized() => Interlocked.Increment(ref initializations);
    public void Disposed() => Interlocked.Increment(ref disposals);
}

internal abstract class TestResource
{
    protected readonly MemoryStream Resource = new([42], writable: false);
    protected TestResource(TestObservation observation)
    {
        Lifetime = new TestLifetime();
        observation.Lifetimes.Add(Lifetime);
    }
    public TestLifetime Lifetime { get; }
    public Task AdmitAsync(CancellationToken token)
    {
        token.ThrowIfCancellationRequested();
        Lifetime.Initialized();
        return Task.CompletedTask;
    }
    public int Use()
    {
        ObjectDisposedException.ThrowIf(!Resource.CanRead, this);
        return Resource.ToArray()[0];
    }
}

internal sealed class SyncResource(TestObservation observation) : TestResource(observation), IDisposable
{
    public void Dispose()
    {
        Lifetime.Disposed();
        Resource.Dispose();
    }
}

internal sealed class AsyncResource(TestObservation observation) : TestResource(observation), IAsyncDisposable, IShellInitializer
{
    public Task InitializeAsync(CancellationToken token = default) => AdmitAsync(token);
    public ValueTask DisposeAsync()
    {
        Lifetime.Disposed();
        return Resource.DisposeAsync();
    }
}

internal sealed class SyncAdmission(SyncResource owner) : IShellInitializer
{
    public Task InitializeAsync(CancellationToken token = default) => owner.AdmitAsync(token);
}

internal sealed class AsyncAdmission(AsyncResource owner) : IShellInitializer
{
    public Task InitializeAsync(CancellationToken token = default) => owner.AdmitAsync(token);
}

[ShellFeature("Ownership.Sync")]
public sealed class SyncFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<SyncResource>();
        services.AddShellInitializer<SyncAdmission>(LifecyclePhase.Prepare, order: 200);
    }
}

[ShellFeature("Ownership.Scoped")]
public sealed class ScopedFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddScoped<AsyncResource>();
        services.AddShellInitializer<AsyncAdmission>(LifecyclePhase.Prepare, order: 200);
    }
}

[ShellFeature("Ownership.Transient")]
public sealed class TransientFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddTransient<AsyncResource>();
        services.AddShellInitializer<AsyncAdmission>(LifecyclePhase.Prepare, order: 200);
    }
}

[ShellFeature("Ownership.BadPhasedSingleton")]
public sealed class BadPhasedSingletonFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<AsyncResource>();
        services.AddShellInitializer<AsyncResource>(LifecyclePhase.Prepare, order: 200);
    }
}

[ShellFeature("Ownership.BadMatchingAlias")]
public sealed class BadMatchingAliasFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<AsyncResource>();
        services.AddSingleton<IShellInitializer>(provider => provider.GetRequiredService<AsyncResource>());
    }
}
