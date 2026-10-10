using CShells.AspNetCore.Configuration;
using CShells.DependencyInjection;
using CShells.Features;
using CShells.Lifecycle;
using Orbyss.Foundation.Tasks;
using Orbyss.Foundation.DomainEvents;

var registrationOrders = new HashSet<string>();
ProbeState.BreakSchemaOrder = args.Contains("--break-schema-order", StringComparer.Ordinal);
foreach (var reverse in new[] { false, true })
foreach (var failure in new[] { "none", "schema", "signing", "startup" })
{
    ProbeState.Reset(failure);
    var configuration = new Dictionary<string, string?>();
    var features = new[] { reverse ? "ZProvider" : "AProvider", reverse ? "Application" : "ApplicationAfter", "FoundationTasks" };
    if (reverse) Array.Reverse(features);
    foreach (var feature in features) configuration[$"CShells:Shells:notes:Features:{feature}"] = "true";
    // A warranted preset declares only reusable selection, with no runtime orchestration.
    if (!reverse)
    {
        configuration.Clear(); configuration["CShells:Shells:notes:Features:NotesPreset"] = "true";
    }
    var builder = WebApplication.CreateBuilder();
    builder.Logging.ClearProviders();
    builder.Configuration.AddInMemoryCollection(configuration);
    builder.Services.AddCShells(shells => shells.WithAssemblies(typeof(Program).Assembly, typeof(FoundationTasksFeature).Assembly)
        .WithConfigurationProvider(builder.Configuration));
    await using var host = builder.Build();
    var registry = host.Services.GetRequiredService<IShellRegistry>();
    registry.Subscribe(new FaultingNotification());
    IShell? shell = null;
    Exception? activationFailure = null;
    try { shell = await registry.GetOrActivateAsync("notes"); }
    catch (Exception error) when (failure != "none") { activationFailure = error; }
    registrationOrders.Add(string.Join(",", ProbeState.Registrations));
    if (failure != "none")
    {
        Require(shell is null, failure + " admitted an active shell");
        Require(registry.GetActive("notes") is null, failure + " left an active shell in the registry");
        Require(activationFailure is not null && Exceptions(activationFailure).Any(e => e.Message == failure + " rejected"), "activation failed for an unrelated cause");
        Require(ProbeState.Events.Contains(failure == "signing" ? "policy" : failure), "intended failure stage was not reached");
        Require(ProbeState.ProviderDisposed, "failed preparation/admission leaked provider scope");
        if (failure == "startup") Require(ProbeState.StartupDisposed, "failed startup leaked scope");
        Require(!ProbeState.Events.Contains("worker"), failure + " started a worker");
        if (failure == "schema") Require(!ProbeState.Events.Contains("policy"), "schema failure admitted policy");
        continue;
    }
    Require(shell is not null && shell.State == ShellLifecycleState.Active, "readiness was not established");
    Require(ProbeState.Events.Take(4).SequenceEqual(new[] { "schema", "policy", "startup", "worker" }), "phase ordering depends on registration order");
    Require(ProbeState.ProviderDisposed, "provider preparation scope survived admission");
    Require(ProbeState.StartupDisposed, "startup scope survived worker start");
    Require(ProbeState.WorkerScopes.Distinct().Count() == 2, "worker reused a scoped provider");
    Require(ProbeState.WorkerScopesDisposed == 2, "worker iterations leaked their owned scopes");
    await using (var scope = shell!.ServiceProvider.CreateAsyncScope())
    {
        var publisher = scope.ServiceProvider.GetRequiredService<IDomainEventPublisher>();
        await publisher.PublishAsync(new NoSubscribers("immutable fact"));
        await publisher.PublishAsync(new NoteSaved("note-1"));
        Require(ProbeState.Events.Contains("reaction:note-1"), "publisher did not await the independent business reaction");
    }
    using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(5));
    var drain = await registry.DrainAsync(shell!, timeout.Token);
    await drain.WaitAsync(timeout.Token);
    Require(ProbeState.Events.Contains("cancelled") && ProbeState.Events.Contains("drained"), "manager did not cancel and await worker drain");
}
Require(registrationOrders.Count == 2, "fixture did not exercise distinct actual feature registration orders");
Console.WriteLine("Actual CShells 0.0.30-preview.159 / Foundation Tasks 0.3.1 lifecycle: registration permutations, schema/signing/startup admission, provider/startup/worker scopes and cancellation/drain passed.");

static void Require(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
static IEnumerable<Exception> Exceptions(Exception error)
{
    yield return error;
    if (error is AggregateException aggregate)
        foreach (var child in aggregate.InnerExceptions) foreach (var nested in Exceptions(child)) yield return nested;
    else if (error.InnerException is not null) foreach (var nested in Exceptions(error.InnerException)) yield return nested;
}

public static class ProbeState
{
    public static List<string> Events { get; } = [];
    public static List<string> Registrations { get; } = [];
    public static List<Guid> WorkerScopes { get; } = [];
    public static string Failure = "none";
    public static bool ProviderDisposed, StartupDisposed;
    public static bool BreakSchemaOrder;
    public static int WorkerScopesDisposed;
    public static void Reset(string failure) { Events.Clear(); Registrations.Clear(); WorkerScopes.Clear(); WorkerScopesDisposed = 0; Failure = failure; ProviderDisposed = StartupDisposed = false; }
}

[ShellFeature("AProvider")]
public class AProviderFeature : ProviderFeature;
public abstract class ProviderFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ProbeState.Registrations.Add("provider");
        services.AddScoped<ProviderSession>();
        services.AddShellInitializer<PrepareProvider>(ProbeState.BreakSchemaOrder ? LifecyclePhase.Default : LifecyclePhase.Prepare, 10);
    }
}
public sealed class ProviderSession : IDisposable
{
    public Guid Id { get; } = Guid.NewGuid();
    public void Dispose() => ProbeState.ProviderDisposed = true;
}
public sealed class PrepareProvider(IServiceScopeFactory scopes) : IShellInitializer
{
    public async Task InitializeAsync(CancellationToken token)
    {
        await using var scope = scopes.CreateAsyncScope();
        _ = scope.ServiceProvider.GetRequiredService<ProviderSession>();
        await Task.Yield(); token.ThrowIfCancellationRequested();
        ProbeState.Events.Add("schema");
        if (ProbeState.Failure == "schema") throw new InvalidOperationException("schema rejected");
    }
}

[ShellFeature("Application")]
public class ApplicationBeforeFeature : ApplicationFeature;
public abstract class ApplicationFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ProbeState.Registrations.Add("application");
        services.AddShellInitializer<PolicyAdmission>(LifecyclePhase.Default, 10);
        services.AddScoped<StartupSession>();
        services.AddScoped<WorkerSession>();
        services.AddScoped<IStartupTask, ApplicationStartup>();
        services.AddSingleton<IBackgroundTask, ApplicationWorker>();
        services.AddFoundationDomainEvents();
        services.AddScoped<IDomainEventHandler<NoteSaved>, NoteSavedReaction>();
    }
}
public sealed class PolicyAdmission : IShellInitializer
{
    public Task InitializeAsync(CancellationToken token)
    {
        if (!ProbeState.Events.Contains("schema")) throw new InvalidOperationException("policy ran before provider");
        ProbeState.Events.Add("policy");
        if (ProbeState.Failure == "signing") throw new InvalidOperationException("signing rejected");
        return Task.CompletedTask;
    }
}
public sealed class StartupSession : IDisposable { public void Dispose() => ProbeState.StartupDisposed = true; }
public sealed class WorkerSession : IDisposable { public Guid Id { get; } = Guid.NewGuid(); public void Dispose() => ProbeState.WorkerScopesDisposed++; }
public sealed class ApplicationStartup(StartupSession session) : IStartupTask
{
    public string Id => "startup";
    public Task ExecuteAsync(CancellationToken token)
    {
        _ = session; ProbeState.Events.Add("startup");
        if (ProbeState.Failure == "startup") throw new InvalidOperationException("startup rejected");
        return Task.CompletedTask;
    }
}
public sealed class ApplicationWorker(IServiceScopeFactory scopes) : IBackgroundTask
{
    public string Id => "worker";
    public async Task ExecuteAsync(CancellationToken token)
    {
        ProbeState.Events.Add("worker");
        for (var iteration = 0; iteration < 2; iteration++)
        {
            await using var scope = scopes.CreateAsyncScope();
            ProbeState.WorkerScopes.Add(scope.ServiceProvider.GetRequiredService<WorkerSession>().Id);
        }
        try { await Task.Delay(Timeout.Infinite, token); }
        catch (OperationCanceledException) when (token.IsCancellationRequested) { ProbeState.Events.Add("cancelled"); }
        finally { ProbeState.Events.Add("drained"); }
    }
}

[ShellFeature("ZProvider", DependsOn = ["Application"])]
public class ZProviderFeature : ProviderFeature;
[ShellFeature("ApplicationAfter", DependsOn = ["AProvider"])]
public class ApplicationAfterFeature : ApplicationFeature;
[ShellFeature("NotesPreset", DependsOn = ["AProvider", "ApplicationAfter", "FoundationTasks"])]
public sealed class NotesPreset : IShellFeature { public void ConfigureServices(IServiceCollection services) { } }
public sealed class FaultingNotification : IShellLifecycleSubscriber
{
    public Task OnStateChangedAsync(IShell shell, ShellLifecycleState previous, ShellLifecycleState current, CancellationToken token)
        => throw new InvalidOperationException("notification is not an admission gate");
}
public sealed record NoteSaved(string Id) : IDomainEvent;
public sealed record NoSubscribers(string Value) : IDomainEvent;
public sealed class NoteSavedReaction : IDomainEventHandler<NoteSaved>
{
    public async ValueTask HandleAsync(NoteSaved fact, DomainEventContext context, CancellationToken token)
    {
        await Task.Yield(); token.ThrowIfCancellationRequested();
        ProbeState.Events.Add("reaction:" + fact.Id);
    }
}
