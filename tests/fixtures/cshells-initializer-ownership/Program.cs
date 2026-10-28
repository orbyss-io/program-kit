using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;
using ProgramKit.Examples.CShellsInitializerOwnership;
using System.Text.Json;

internal static class Program
{
    private static readonly List<object> Results = [];
    private static readonly TimeSpan Limit = TimeSpan.FromSeconds(10);

    public static async Task Main(string[] args)
    {
        try
        {
            await HappyAsync();
            await FailedActivationAsync(cancel: false);
            await FailedActivationAsync(cancel: true);
            await TrackedReloadAsync();
            await FailedReplacementAsync(cancel: false);
            await FailedReplacementAsync(cancel: true);
            await SyncAsync();
            await ShortLivedAsync<ScopedFeature>("scoped-admission-cleanup");
            await ShortLivedAsync<TransientFeature>("transient-admission-cleanup");
            await KnownBadAsync<BadPhasedSingletonFeature>("known-bad-phased-singleton", premature: true);
            await KnownBadAsync<BadMatchingAliasFeature>("known-bad-matching-singleton-alias", premature: false);
            File.WriteAllText(args[0], JsonSerializer.Serialize(new { status = "passed", cases = Results }, new JsonSerializerOptions { WriteIndented = true }));
            Console.WriteLine($"Native ownership safety cases passed: {Results.Count}");
        }
        catch (Exception error)
        {
            File.WriteAllText(args[0], JsonSerializer.Serialize(new { status = "failed", cases = Results, failure = error.ToString() }, new JsonSerializerOptions { WriteIndented = true }));
            throw;
        }
    }

    internal static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private static TaskCompletionSource Barrier() => new(TaskCreationOptions.RunContinuationsAsynchronously);

    private static void Check(ResourceLifetime life, int initialized, int disposed)
    {
        Require(life.Initializations == initialized && life.Disposals == disposed,
            $"Unexpected resource lifetime: {life.Initializations}/{life.Disposals}, expected {initialized}/{disposed}");
    }

    private static void Closed(Action action)
    {
        try { action(); }
        catch (ObjectDisposedException) { return; }
        throw new InvalidOperationException("A disposed resource remained usable");
    }

    private static async Task HappyAsync()
    {
        var observation = new SyntheticResourceObservation();
        var host = ProbeHost.Create<ResourceFeature>(observation);
        try
        {
            var shell = await host.Registry.GetOrActivateAsync("probe").WaitAsync(Limit);
            var owner = shell.ServiceProvider.GetRequiredService<SyntheticResourceOwner>();
            Require(owner.Use() == 42 && observation.Lifetimes.Count == 1, "Shipped owner was not usable after activation");
            Check(owner.Lifetime, 1, 0);
            await host.DisposeGenerationAsync(shell);
            Check(owner.Lifetime, 1, 1);
            Closed(() => owner.Use());
        }
        finally { await host.DisposeAsync(); }
        Check(observation.Lifetimes.Single(), 1, 1);
        Results.Add(new { name = "shipped-async-owner-happy-and-teardown", initialized = 1, disposed = 1 });
    }

    private static async Task FailedActivationAsync(bool cancel)
    {
        var gate = Barrier();
        var original = new InvalidOperationException("Synthetic partial-startup failure");
        var observation = new SyntheticResourceObservation { AdmissionContinuation = gate.Task, Failure = cancel ? null : original };
        using var cancellation = new CancellationTokenSource();
        var host = ProbeHost.Create<ResourceFeature>(observation);
        try
        {
            var activation = host.Registry.GetOrActivateAsync("probe", cancellation.Token);
            await observation.AdmissionEntered.Task.WaitAsync(Limit);
            Require(observation.Lifetimes.Count == 1 && !activation.IsCompleted, "Failure/cancel did not reach pending initialization");
            Check(observation.Lifetimes[0], 1, 0);
            if (cancel) cancellation.Cancel(); else gate.TrySetResult();
            Exception? observed = null;
            try { await activation.WaitAsync(Limit); } catch (Exception error) { observed = error; }
            Require(cancel ? observed is OperationCanceledException canceled && canceled.CancellationToken == cancellation.Token
                : ReferenceEquals(observed, original), "Original initialization failure/cancellation was not preserved");
            Require(host.Registry.GetActive("probe") is null && host.Registry.GetAll("probe").Count == 0,
                "Failed admission published an active or partial generation");
            Check(observation.Lifetimes.Single(), 1, 1);
        }
        finally { gate.TrySetResult(); await host.DisposeAsync(); }
        Check(observation.Lifetimes.Single(), 1, 1);
        Results.Add(new { name = cancel ? "entered-admission-cancellation" : "asynchronous-partial-startup-failure", initialized = 1, disposed = 1 });
    }

    private static async Task TrackedReloadAsync()
    {
        var observation = new SyntheticResourceObservation();
        var host = ProbeHost.Create<ResourceFeature>(observation);
        IShellScope? scope = null;
        try
        {
            var first = await host.Registry.GetOrActivateAsync("probe").WaitAsync(Limit);
            var owner = first.ServiceProvider.GetRequiredService<SyntheticResourceOwner>();
            scope = first.BeginScope();
            var reload = await host.Registry.ReloadAsync("probe").WaitAsync(Limit);
            Require(reload.Error is null && reload.NewShell is not null && reload.Drain is not null, "Successful reload result was not observed");
            var second = reload.NewShell!;
            var next = second.ServiceProvider.GetRequiredService<SyntheticResourceOwner>();
            Require(!ReferenceEquals(first, second) && !ReferenceEquals(owner, next)
                && ReferenceEquals(host.Registry.GetActive("probe"), second), "Reload reused or failed to publish its generation owner");
            Require(owner.Use() == 42 && next.Use() == 42 && observation.Lifetimes.Count == 2,
                "Active tracked scope did not preserve old/new resource usability");
            Check(owner.Lifetime, 1, 0);
            Check(next.Lifetime, 1, 0);
            Require(!reload.Drain!.WaitAsync().IsCompleted, "Drain completed while its tracked scope remained open");
            await scope.DisposeAsync();
            scope = null;
            await reload.Drain.WaitAsync().WaitAsync(Limit);
            await host.DisposeGenerationAsync(first);
            Check(owner.Lifetime, 1, 1);
            Check(next.Lifetime, 1, 0);
            Closed(() => owner.Use());
            Require(next.Use() == 42, "Old-generation teardown closed the replacement owner");
            await host.DisposeGenerationAsync(second);
            Check(next.Lifetime, 1, 1);
        }
        finally
        {
            if (scope is not null) await scope.DisposeAsync();
            await host.DisposeAsync();
        }
        Require(observation.Lifetimes.All(life => life.Disposals == 1), "Root disposal repeated generation cleanup");
        Results.Add(new { name = "reload-with-active-tracked-scope", generations = 2, disposalsPerGeneration = 1 });
    }

    private static async Task FailedReplacementAsync(bool cancel)
    {
        var observation = new SyntheticResourceObservation();
        var host = ProbeHost.Create<ResourceFeature>(observation);
        var gate = Barrier();
        using var cancellation = new CancellationTokenSource();
        try
        {
            var first = await host.Registry.GetOrActivateAsync("probe").WaitAsync(Limit);
            var owner = first.ServiceProvider.GetRequiredService<SyntheticResourceOwner>();
            var original = new InvalidOperationException("Synthetic replacement rejection");
            observation.AdmissionEntered = Barrier();
            observation.AdmissionContinuation = gate.Task;
            observation.Failure = cancel ? null : original;
            var replacing = host.Registry.ReloadAsync("probe", cancellation.Token);
            await observation.AdmissionEntered.Task.WaitAsync(Limit);
            Require(!replacing.IsCompleted && observation.Lifetimes.Count == 2, "Replacement did not reach pending initialization");
            if (cancel) cancellation.Cancel(); else gate.TrySetResult();
            var reload = await replacing.WaitAsync(Limit);
            Require(reload.NewShell is null && reload.Drain is null && (cancel
                ? reload.Error is OperationCanceledException canceled && canceled.CancellationToken == cancellation.Token
                : ReferenceEquals(reload.Error, original)), "Replacement did not preserve its original failure/cancellation");
            Require(ReferenceEquals(host.Registry.GetActive("probe"), first)
                && host.Registry.GetAll("probe").Count == 1 && owner.Use() == 42,
                "Rejected replacement changed the active generation");
            Check(owner.Lifetime, 1, 0);
            Check(observation.Lifetimes[1], 1, 1);
            await host.DisposeGenerationAsync(first);
        }
        finally { gate.TrySetResult(); await host.DisposeAsync(); }
        Require(observation.Lifetimes.All(life => life.Initializations == 1 && life.Disposals == 1), "Replacement cleanup was repeated or missing");
        Results.Add(new { name = cancel ? "canceled-replacement-preserves-old-generation" : "failed-replacement-preserves-old-generation", disposalsPerGeneration = 1 });
    }

    private static async Task SyncAsync()
    {
        var observation = new TestObservation();
        var host = ProbeHost.Create<SyncFeature>(new SyntheticResourceObservation(), observation);
        try
        {
            var shell = await host.Registry.GetOrActivateAsync("probe").WaitAsync(Limit);
            var owner = shell.ServiceProvider.GetRequiredService<SyncResource>();
            Require(owner.Use() == 42 && owner.Lifetime.Initializations == 1 && owner.Lifetime.Disposals == 0, "Sync adapter disposed its owner at activation");
            await host.DisposeGenerationAsync(shell);
            Closed(() => owner.Use());
        }
        finally { await host.DisposeAsync(); }
        Require(observation.Lifetimes.Single().Disposals == 1, "Sync owner was not disposed exactly once");
        Results.Add(new { name = "sync-owner-nondisposable-admission", disposed = 1 });
    }

    private static async Task ShortLivedAsync<TFeature>(string name) where TFeature : class, CShells.Features.IShellFeature
    {
        var observation = new TestObservation();
        var host = ProbeHost.Create<TFeature>(new SyntheticResourceObservation(), observation);
        try
        {
            await host.Registry.GetOrActivateAsync("probe").WaitAsync(Limit);
            Require(observation.Lifetimes.Count == 1 && observation.Lifetimes[0].Initializations == 1
                && observation.Lifetimes[0].Disposals == 1, "Initializer-only scoped/transient resource was not cleaned once at scope exit");
        }
        finally { await host.DisposeAsync(); }
        Require(observation.Lifetimes.Single().Disposals == 1, "Short-lived resource cleanup repeated at generation teardown");
        Results.Add(new { name, disposedAtInitializationScopeExit = 1, runtimeResourceClaim = false });
    }

    private static async Task KnownBadAsync<TFeature>(string name, bool premature) where TFeature : class, CShells.Features.IShellFeature
    {
        var observation = new TestObservation();
        var host = ProbeHost.Create<TFeature>(new SyntheticResourceObservation(), observation);
        try
        {
            var shell = await host.Registry.GetOrActivateAsync("probe").WaitAsync(Limit);
            var owner = shell.ServiceProvider.GetRequiredService<AsyncResource>();
            Require(owner.Lifetime.Initializations == 1 && owner.Lifetime.Disposals == (premature ? 1 : 0), "Known defective registration no longer matches its exact version-scoped behavior");
            if (premature) Closed(() => owner.Use()); else Require(owner.Use() == 42, "Alias control was not usable before teardown");
            await host.DisposeGenerationAsync(shell);
        }
        finally { await host.DisposeAsync(); }
        Require(observation.Lifetimes.Single().Disposals == 2, "Known duplicate ownership was not actually reproduced");
        Results.Add(new { name, negativeControl = true, prematureDisposal = premature, disposed = 2 });
    }
}
