// Non-shipping runtime counterexamples intentionally include incorrect implementations.
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Schema;
using System.Threading.Channels;
using System.Xml.Linq;
using Microsoft.Extensions.DependencyInjection;

var cases = new (string Name, Func<Task> Run)[]
{
    ("async_completion_owns_disposal", Cases.AsyncDisposal),
    ("all_child_faults_are_observed", Cases.FaultObservation),
    ("successful_acquire_pairs_release", Cases.SemaphoreOwnership),
    ("compound_shared_state_needs_coordination", Cases.SharedState),
    ("bounded_channel_cancellation_and_completion", Cases.ChannelOwnership),
    ("lazy_factory_and_cached_failure", Cases.LazyFailure),
    ("lazy_task_shared_cancellation", Cases.LazyCancellation),
    ("publication_only_loser_ownership", Cases.PublicationOwnership),
    ("di_scope_and_partial_construction_cleanup", Cases.ScopeOwnership),
    ("typed_strict_request_tolerant_response", Cases.TypedJson),
    ("api_v1_v2_schema_and_snapshot_compatibility", Cases.ApiEvolution),
    ("record_shallow_immutability_is_not_deep", Cases.RecordOwnership),
    ("query_cardinality_and_snapshot", Cases.QueryMeaning),
    ("controlled_time_and_protocol_identity", Cases.ControlledTime),
    ("bounded_input_and_path_admission", Cases.InputAdmission),
    ("semantic_capability_substitution", Cases.Substitution)
};
var suite = new XElement("testsuite");
var failed = false;
foreach (var test in cases)
{
    var item = new XElement("testcase", new XAttribute("classname", "Engineering"), new XAttribute("name", test.Name));
    try { await test.Run().WaitAsync(TimeSpan.FromSeconds(15)); }
    catch (Exception error) { failed = true; item.Add(new XElement("failure", error.ToString())); }
    suite.Add(item);
}
new XDocument(suite).Save(args[0]);
return failed ? 1 : 0;

internal static class Cases
{
    public static async Task AsyncDisposal()
    {
        static Task Unsafe(Lease lease, Task gate) { using (lease) return Use(lease, gate); }
        static async Task Safe(Lease lease, Task gate) { using (lease) await Use(lease, gate); }
        static async Task Use(Lease lease, Task gate) { await gate; Check(!lease.Disposed, "resource disposed before asynchronous completion"); }
        var gate = Signal(); var bad = new Lease(); var pending = Unsafe(bad, gate.Task);
        gate.SetResult(); await Reject<InvalidOperationException>(() => pending);
        gate = Signal(); var good = new Lease(); pending = Safe(good, gate.Task);
        Check(!good.Disposed, "safe operation disposed early"); gate.SetResult(); await pending;
        Check(good.Disposed, "safe operation did not dispose");
    }

    public static async Task FaultObservation()
    {
        var all = Task.WhenAll(Task.FromException(new InvalidOperationException("first")),
                              Task.FromException(new ArgumentException("second")));
        await Reject<InvalidOperationException>(() => all);
        Check(all.Exception!.InnerExceptions.Count == 2, "lost child outcome");
    }

    public static async Task SemaphoreOwnership()
    {
        using var gate = new SemaphoreSlim(1, 1);
        using var cancelled = new CancellationTokenSource(); cancelled.Cancel();
        // A finally outside successful acquisition incorrectly releases someone else's permit.
        await Reject<SemaphoreFullException>(async () =>
        {
            try { await gate.WaitAsync(cancelled.Token); }
            finally { gate.Release(); }
        });
        await Reject<OperationCanceledException>(async () =>
        {
            await gate.WaitAsync(cancelled.Token);
            try { throw new InvalidOperationException(); }
            finally { gate.Release(); }
        });
        await gate.WaitAsync();
        try { Check(gate.CurrentCount == 0, "permit not acquired"); }
        finally { gate.Release(); }
        Check(gate.CurrentCount == 1, "permit leaked");
    }

    public static async Task SharedState()
    {
        var value = 0; var firstRead = Signal(); var secondRead = Signal(); var release = Signal();
        async Task Broken(TaskCompletionSource ready)
        {
            var observed = value; ready.SetResult(); await release.Task; value = observed + 1;
        }
        var first = Broken(firstRead); var second = Broken(secondRead);
        await Task.WhenAll(firstRead.Task, secondRead.Task); release.SetResult(); await Task.WhenAll(first, second);
        Check(value == 1, "counterexample did not force a lost update");
        value = 0;
        await Task.WhenAll(Task.Run(() => Interlocked.Increment(ref value)), Task.Run(() => Interlocked.Increment(ref value)));
        Check(value == 2, "atomic increments lost state");
    }

    public static async Task ChannelOwnership()
    {
        var channel = Channel.CreateBounded<int>(new BoundedChannelOptions(1) { FullMode = BoundedChannelFullMode.Wait });
        await channel.Writer.WriteAsync(1);
        using var cancel = new CancellationTokenSource();
        var pending = channel.Writer.WriteAsync(2, cancel.Token).AsTask();
        Check(!pending.IsCompleted, "bounded producer did not wait"); cancel.Cancel();
        await Reject<OperationCanceledException>(() => pending);
        Check(await channel.Reader.ReadAsync() == 1, "cancelled producer replaced retained data");
        channel.Writer.Complete(); await channel.Reader.Completion;
        Check(!channel.Writer.TryWrite(3), "write after completion was admitted");
    }

    public static Task LazyFailure()
    {
        var count = 0;
        var value = new Lazy<int>(() => { count++; throw new InvalidOperationException("factory"); },
                                  LazyThreadSafetyMode.ExecutionAndPublication);
        for (var i = 0; i < 2; i++)
        {
            try { _ = value.Value; throw new Exception("fault unexpectedly recovered"); }
            catch (InvalidOperationException) { }
        }
        Check(count == 1 && !value.IsValueCreated, "factory exception caching changed");
        var good = new Lazy<Lease>(() => new Lease());
        Check(!good.IsValueCreated, "initialization was not deferred");
        using var owned = good.Value;
        Check(ReferenceEquals(owned, good.Value), "value not shared");
        return Task.CompletedTask;
    }

    public static async Task LazyCancellation()
    {
        using var cancellation = new CancellationTokenSource(); cancellation.Cancel();
        var count = 0;
        var value = new Lazy<Task<int>>(() => { count++; return Task.FromCanceled<int>(cancellation.Token); });
        await Reject<OperationCanceledException>(() => value.Value);
        await Reject<OperationCanceledException>(() => value.Value);
        Check(count == 1 && value.IsValueCreated, "cancelled task was not cached");
        var shared = new Lazy<Task<int>>(() => Task.FromResult(42));
        Check(await shared.Value == 42, "independent initialization failed");
    }

    public static async Task PublicationOwnership()
    {
        var values = new System.Collections.Concurrent.ConcurrentBag<Lease>();
        using var ready = new CountdownEvent(2); using var release = new ManualResetEventSlim();
        var lazy = new Lazy<Lease>(() =>
        {
            var created = new Lease(); values.Add(created); ready.Signal();
            if (!release.Wait(TimeSpan.FromSeconds(5))) throw new TimeoutException();
            return created;
        }, LazyThreadSafetyMode.PublicationOnly);
        var a = Task.Run(() => lazy.Value); var b = Task.Run(() => lazy.Value);
        try { Check(ready.Wait(TimeSpan.FromSeconds(5)), "both factories did not enter"); }
        finally { release.Set(); }
        await Task.WhenAll(a, b);
        Check(values.Count == 2 && ReferenceEquals(a.Result, b.Result), "publication did not choose one value");
        Check(values.All(v => !v.Disposed), "Lazy unexpectedly owned losing disposal");
        foreach (var value in values) value.Dispose();
        Check(values.All(v => v.Disposed), "explicit owner leaked a created value");
    }

    public static Task ScopeOwnership()
    {
        var services = new ServiceCollection(); services.AddScoped<Lease>(); services.AddSingleton<Captive>();
        try { using var invalid = services.BuildServiceProvider(new ServiceProviderOptions { ValidateScopes = true, ValidateOnBuild = true });
              throw new InvalidOperationException("captive dependency admitted"); }
        catch (AggregateException) { }
        services = new ServiceCollection(); services.AddScoped<Lease>();
        using var provider = services.BuildServiceProvider(new ServiceProviderOptions { ValidateScopes = true });
        Lease owned;
        using (var scope = provider.CreateScope()) owned = scope.ServiceProvider.GetRequiredService<Lease>();
        Check(owned.Disposed, "scope did not dispose its service");
        var partial = new Lease();
        try { try { throw new ArgumentException("second resource failed"); } finally { partial.Dispose(); } }
        catch (ArgumentException) { }
        Check(partial.Disposed, "partial construction leaked");
        return Task.CompletedTask;
    }

    public static Task TypedJson()
    {
        var strict = new JsonSerializerOptions { UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
        const string payload = "{\"Id\":\"R1\",\"Count\":2,\"Unknown\":true}";
        try { JsonSerializer.Deserialize<Reservation>(payload, strict); throw new InvalidOperationException("unknown request field admitted"); }
        catch (JsonException) { }
        Check(JsonSerializer.Deserialize<Reservation>(payload) == new Reservation("R1", 2), "old response reader broke on an additive field");
        using var dynamicDocument = JsonDocument.Parse("{\"custom-property\":7}");
        Check(dynamicDocument.RootElement.GetProperty("custom-property").GetInt32() == 7, "bounded dynamic schema wrongly forbidden");
        return Task.CompletedTask;
    }

    public static Task RecordOwnership()
    {
        var items = new List<int> { 1 }; var shallow = new Snapshot(items); items.Add(2);
        Check(shallow.Items.Count == 2, "counterexample did not demonstrate shallow ownership");
        var owned = new Snapshot(items.ToArray()); items.Add(3);
        Check(owned.Items.Count == 2, "snapshot retained caller mutation");
        Check(default(Quantity).Value == 0, "value default was overlooked");
        return Task.CompletedTask;
    }

    public static Task ApiEvolution()
    {
        var options = new JsonSerializerOptions(JsonSerializerOptions.Default)
        {
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
            RespectRequiredConstructorParameters = true
        };
        var schema = options.GetJsonSchemaAsNode(typeof(Reservation));
        Check(schema["additionalProperties"]!.GetValue<bool>() == false, "schema allows rejected request members");
        Check(schema["properties"]!["Count"]!["type"]!.GetValue<string>() == "integer", "typed count lost schema parity");
        var original = JsonSerializer.Serialize(new Reservation("R1", 2));
        var evolved = JsonSerializer.Deserialize<ReservationV2>(original)!;
        Check(evolved.Id == "R1" && evolved.Note is null, "stored V1 snapshot no longer readable");
        var response = JsonSerializer.Serialize(evolved with { Note = "new additive response" });
        Check(JsonSerializer.Deserialize<Reservation>(response) == new Reservation("R1", 2), "old response client rejected additive field");
        try { JsonSerializer.Deserialize<Reservation>(response, options); throw new InvalidOperationException("V2 request silently admitted by strict V1 parser"); }
        catch (JsonException) { }
        // A breaking DTO change fails the old wire shape; it needs a distinct admitted version boundary.
        try { JsonSerializer.Deserialize<BreakingReservation>(original, options); throw new InvalidOperationException("renamed field silently broke snapshot identity"); }
        catch (JsonException) { }
        Check(JsonSerializer.Serialize(new Reservation(evolved.Id, evolved.Count)) == original,
              "canonical V1 identity changed during additive projection");
        return Task.CompletedTask;
    }

    public static Task QueryMeaning()
    {
        var source = new List<int> { 1, 2 }; var deferred = source.Where(n => n > 1); var snapshot = deferred.ToArray();
        source.Add(3);
        Check(deferred.Count() == 2 && snapshot.Single() == 2, "materialization boundary did not preserve snapshot");
        try { _ = deferred.Single(); throw new Exception("multiple results admitted as single"); }
        catch (InvalidOperationException) { }
        return Task.CompletedTask;
    }

    public static Task ControlledTime()
    {
        var clock = new ControlledClock(); var start = clock.GetTimestamp(); clock.Advance(TimeSpan.FromSeconds(7));
        Check(clock.GetElapsedTime(start) == TimeSpan.FromSeconds(7), "elapsed-time seam ignored");
        var before = CultureInfo.CurrentCulture;
        try { CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("tr-TR");
              Check(string.Equals("FILE", "file", StringComparison.OrdinalIgnoreCase), "protocol identity depends on culture"); }
        finally { CultureInfo.CurrentCulture = before; }
        return Task.CompletedTask;
    }

    public static Task InputAdmission()
    {
        static bool Admitted(string text) => text.Length <= 32 && System.Text.RegularExpressions.Regex.IsMatch(
            text, "^[a-z0-9-]+$", System.Text.RegularExpressions.RegexOptions.NonBacktracking, TimeSpan.FromMilliseconds(100));
        Check(Admitted("reservation-1") && !Admitted(new string('a', 33)) && !Admitted("../secret"), "input bound or grammar ignored");
        var root = Path.GetFullPath("owned"); var escaped = Path.GetRelativePath(root, Path.GetFullPath(Path.Combine(root, "../secret")));
        Check(escaped.StartsWith("..", StringComparison.Ordinal), "traversal not identified");
        return Task.CompletedTask;
    }

    public static Task Substitution()
    {
        static bool Contract(Func<int, int> admit) => admit(0) == 0 && admit(2) is >= 0 and <= 2;
        Check(Contract(capacity => Math.Min(capacity, 1)), "valid policy substitution rejected");
        Check(!Contract(capacity => capacity + 1), "invalid policy substitution passed");
        return Task.CompletedTask;
    }

    private static TaskCompletionSource Signal() => new(TaskCreationOptions.RunContinuationsAsynchronously);
    private static void Check(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
    private static async Task Reject<T>(Func<Task> operation) where T : Exception
    {
        try { await operation(); }
        catch (T) { return; }
        throw new InvalidOperationException("Expected rejection: " + typeof(T).Name);
    }
}

internal sealed class Lease : IDisposable { public bool Disposed { get; private set; } public void Dispose() => Disposed = true; }
internal sealed class Captive(Lease lease) { public Lease Dependency { get; } = lease; }
internal sealed record Reservation(string Id, int Count);
internal sealed record ReservationV2(string Id, int Count, string? Note = null);
internal sealed record BreakingReservation(string ReservationId, int Count);
internal sealed record Snapshot(IReadOnlyList<int> Items);
internal readonly record struct Quantity(int Value);
internal sealed class ControlledClock : TimeProvider
{
    private long ticks;
    public override long TimestampFrequency => TimeSpan.TicksPerSecond;
    public override long GetTimestamp() => ticks;
    public void Advance(TimeSpan duration) => ticks += duration.Ticks;
}
