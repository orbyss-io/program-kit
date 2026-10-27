using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using ProgramKit.Examples.TypedOperation;

var clock = new ControlledClock();
var store = new Store(clock);
var values = new Dictionary<string, string?> { ["Sample:Execution:Timeout"] = "00:00:03" };
var builder = new ConfigurationBuilder();
var configuration = builder
    .AddInMemoryCollection(values)
    .Build();
var services = new ServiceCollection();
services.AddSingleton<TimeProvider>(clock);
Func<IServiceProvider, ILabelStore> createStore = _ => store;
services.AddScoped<ILabelStore>(createStore);
LabelServices.Configure(services, configuration);
var providerOptions = new ServiceProviderOptions { ValidateScopes = true };
using var provider = services.BuildServiceProvider(providerOptions);
using var scope = provider.CreateScope();
var operations = scope.ServiceProvider.GetRequiredService<ILabelOperations>();
var sameOperation = scope.ServiceProvider.GetRequiredService<ILabelOperations>();
using var otherScope = provider.CreateScope();
var otherOperation = otherScope.ServiceProvider.GetRequiredService<ILabelOperations>();
var sameScopeIdentity = ReferenceEquals(operations, sameOperation);
var differentScopeIdentity = !ReferenceEquals(operations, otherOperation);
Check(sameScopeIdentity, "one operation per scope");
Check(differentScopeIdentity, "separate operation per scope");
var initial = await operations.ReadAsync(CancellationToken.None);
Check(initial == "ready", "initial label representation");
store.Reset();
var updated = await operations.UpdateAsync("edited", CancellationToken.None);
Check(updated == "edited" && store.Value == "edited", "committed label representation");
Check(store.Writes == 1 && store.Reads == 1, "write and observation exactly once");
Check(store.WriteToken == store.ReadToken, "same outer token for write and observation");
store.Reset();

// Both stages fit individually, but cannot restart the whole three-second cap.
store.WriteCost = TimeSpan.FromSeconds(2);
store.ReadCost = TimeSpan.FromSeconds(2);
Func<Task> completeUpdate = () => operations.UpdateAsync("committed", CancellationToken.None);
await Reject<TimeoutException>(completeUpdate);
Check(store.Value == "committed" && store.Writes == 1 && store.Reads == 1, "expiry does not undo/retry");
Check(store.WriteToken == store.ReadToken && store.ReadToken.IsCancellationRequested, "one bounded outer token");

// A non-cooperating write may complete, but no fresh read starts after expiry.
store.Reset();
store.WriteCost = TimeSpan.FromSeconds(4);
Func<Task> lateUpdate = () => operations.UpdateAsync("late-write", CancellationToken.None);
await Reject<TimeoutException>(lateUpdate);
Check(store.Value == "late-write" && store.Writes == 1 && store.Reads == 0, "late write cannot start observation");

// A non-cooperating read may return data; freshness still rejects late success.
store.Reset();
store.ReadCost = TimeSpan.FromSeconds(4);
Func<Task> readOperation = () => operations.ReadAsync(CancellationToken.None);
await Reject<TimeoutException>(readOperation);
Check(store.Reads == 1, "late read executed only once");

clock.DelayCallbacks = true;
store.Reset();
store.ReadCost = TimeSpan.FromSeconds(4);
await Reject<TimeoutException>(readOperation);
Check(!store.TokenWasCanceledAtReturn, "delayed callback is independent from monotonic expiry");
clock.DelayCallbacks = false;

store.Reset();
using var caller = new CancellationTokenSource();
store.CancelDuringRead = caller;
Func<Task> callerRead = () => operations.ReadAsync(caller.Token);
await Reject<OperationCanceledException>(callerRead);
Check(store.Reads == 1, "caller cancellation stays cancellation");
store.Reset();
caller.Cancel();
Func<Task> canceledWrite = () => operations.UpdateAsync("never", caller.Token);
await Reject<OperationCanceledException>(canceledWrite);
Check(store.Writes == 0 && store.Reads == 0, "canceled caller has no effects");

store.Reset();
store.ReadCost = TimeSpan.FromSeconds(1);
var read = await operations.ReadAsync(CancellationToken.None);
Check(read == store.Value, "within-budget completion");
var registeredClock = provider.GetRequiredService<TimeProvider>();
Check(registeredClock == clock, "native registration preserves clock owner");

// Omission and exact native timer bounds are exercised through real registration
// and execution, including expiry at the accepted boundary.
var defaultBudget = TimeSpan.FromSeconds(30);
await CheckBudgetBoundary(null, defaultBudget);
var maximumBudget = TimeSpan.FromMilliseconds(uint.MaxValue - 1d);
var maximumText = maximumBudget.ToString("c", System.Globalization.CultureInfo.InvariantCulture);
await CheckBudgetBoundary(maximumText, maximumBudget);

// Invalid runtime configuration is observed before the first effect.
var unsupportedBudget = TimeSpan.FromMilliseconds(uint.MaxValue);
var unsupportedText = unsupportedBudget.ToString("c", System.Globalization.CultureInfo.InvariantCulture);
string[] invalidDurations = ["00:00:00", unsupportedText];
foreach (var invalidDuration in invalidDurations)
{
    var invalidServices = new ServiceCollection();
    invalidServices.AddScoped<ILabelStore>(createStore);
    values["Sample:Execution:Timeout"] = invalidDuration;
    var invalidBuilder = new ConfigurationBuilder();
    var invalidConfiguration = invalidBuilder
        .AddInMemoryCollection(values)
        .Build();
    LabelServices.Configure(invalidServices, invalidConfiguration);
    using var invalidProvider = invalidServices.BuildServiceProvider();
    var invalid = invalidProvider.GetRequiredService<ILabelOperations>();
    store.Reset();
    Func<Task> invalidWrite = () => invalid.UpdateAsync("never", CancellationToken.None);
    await Reject<OptionsValidationException>(invalidWrite);
    Check(store.Writes == 0 && store.Reads == 0, "invalid options have no effects");
}
Console.WriteLine("NATIVE_OUTER_DEADLINE_FRESHNESS_CALLER_AND_CONFIG_PASSED");

static void Check(bool condition, string message)
{
    if (!condition)
        throw new InvalidOperationException(message);
}

static async Task Reject<T>(Func<Task> operation) where T : Exception
{
    try
    {
        await operation();
    }
    catch (T)
    {
        return;
    }
    throw new InvalidOperationException("Expected " + typeof(T).Name);
}

static async Task CheckBudgetBoundary(string? configured, TimeSpan expected)
{
    var boundaryClock = new ControlledClock();
    var boundaryStore = new Store(boundaryClock) { ReadCost = expected };
    var boundaryValues = new Dictionary<string, string?>();
    if (configured is not null)
        boundaryValues["Sample:Execution:Timeout"] = configured;
    var boundaryBuilder = new ConfigurationBuilder();
    var boundaryConfiguration = boundaryBuilder
        .AddInMemoryCollection(boundaryValues)
        .Build();
    var boundaryServices = new ServiceCollection();
    boundaryServices.AddSingleton<TimeProvider>(boundaryClock);
    Func<IServiceProvider, ILabelStore> createBoundaryStore = _ => boundaryStore;
    boundaryServices.AddScoped<ILabelStore>(createBoundaryStore);
    LabelServices.Configure(boundaryServices, boundaryConfiguration);
    using var boundaryProvider = boundaryServices.BuildServiceProvider();
    var boundOptions = boundaryProvider.GetRequiredService<IOptions<LabelExecutionOptions>>();
    Check(boundOptions.Value.Timeout == expected, "effective registered option boundary");
    var boundaryOperation = boundaryProvider.GetRequiredService<ILabelOperations>();
    Func<Task> boundaryRead = () => boundaryOperation.ReadAsync(CancellationToken.None);
    await Reject<TimeoutException>(boundaryRead);
    Check(boundaryStore.Reads == 1, "admitted boundary reaches native execution and expires");
}
