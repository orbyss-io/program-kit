using System.Security.Cryptography;
using System.Text;
using Synthetic.BatchProcessing.Core;

// Console conformance fixture, NOT a replacement application host or durable provider.
var now = DateTimeOffset.Parse("2026-01-01T00:00:00Z");
var scope = "Development.tenant-a";
var execution = new ProviderBinding("Recording.Execution", "1.0.0", "1", scope);
var exchange = new ProviderBinding("Recording.Exchange", "1.0.0", "1", scope);
Attempt NewAttempt(string id = "batch-a", int generation = 1) =>
    new(id, generation, now.AddMinutes(5), execution, exchange);
void Check(bool value, string name)
{
    if (!value) throw new Exception("CONFORMANCE_FAILED " + name);
    Console.WriteLine("PASS " + name);
}

var authority = new Authorization();
var inputs = new RecordingExchange(exchange, authority);
var worker = new RecordingExecution(execution);
var work = NewAttempt(); authority.Admit(work);
var snapshot = inputs.Capture(work, "synthetic batch", now);
Check(inputs.Read(work, snapshot, now) == "synthetic batch", "authorized-snapshot-read");
var coordinator = new Coordinator(work, snapshot);
Check(coordinator.PendingDispatch && worker.StartCount == 0, "admission-records-intent-before-dispatch-model-only");
worker.LoseAcknowledgement = true;
coordinator.Dispatch(worker, now);
Check(coordinator.PendingDispatch && coordinator.Submission == Submission.Unknown && worker.StartCount == 1,
    "lost-acknowledgement-remains-unknown");
coordinator.Dispatch(worker, now.AddSeconds(2));
Check(!coordinator.PendingDispatch && worker.StartCount == 1, "same-attempt-retry-does-not-start-duplicate");
Check(worker.Observe(work) == ExecutionState.Running, "observe-original-submission");
var result = new ProcessingResult("result-a", snapshot.Sha256);
Check(inputs.Publish(work, result, now) && inputs.Publish(work, result, now) && inputs.PublishCount == 1,
    "duplicate-result-is-idempotent");
Check(!inputs.Publish(work, result with { Sha256 = "different" }, now), "conflicting-result-is-rejected");
Check(!inputs.Publish(work with { Exchange = exchange with { Scope = "Production.tenant-b" } }, result, now),
    "wrong-scope-rejected-at-effect-owner");

var next = NewAttempt(generation: 2); authority.Admit(next);
Check(!inputs.Publish(work, result, now), "superseded-attempt-cannot-publish");
try { inputs.Read(work, snapshot, now); Check(false, "stale-read"); }
catch (InvalidOperationException) { Check(true, "superseded-attempt-cannot-read"); }
Check(!inputs.Publish(next, result, next.Deadline), "original-deadline-fences-publication");
var delayed = new Coordinator(next, snapshot); delayed.Dispatch(worker, next.Deadline);
Check(delayed.PendingDispatch && worker.StartCount == 1, "expired-dispatch-does-not-reset-deadline");
authority.Cancel(next);
Check(!inputs.Publish(next, result, now), "cancellation-fences-result-before-stop-confirmed");
worker.RequestStop(work);
Check(worker.Observe(work) == ExecutionState.Running && !worker.Cleanup(work),
    "stop-request-is-not-stop-confirmation-or-cleanup");
worker.ConfirmStopped(work);
worker.Unavailable = true;
Check(!coordinator.Cleanup(worker, inputs) && coordinator.CleanupPending, "outage-retains-cleanup-obligation");
worker.Unavailable = false;
Check(coordinator.Cleanup(worker, inputs) && !coordinator.CleanupPending,
    "confirmed-stop-and-exchange-erasure-complete-cleanup");
Check(coordinator.Cleanup(worker, inputs), "cleanup-is-idempotent");

var deletion = NewAttempt("batch-delete"); authority.Admit(deletion);
inputs.Capture(deletion, "synthetic deletion", now); authority.Delete(deletion.WorkId);
Check(!inputs.Publish(deletion, result, now) && inputs.Erase(deletion), "deletion-fences-late-result-and-erases-model-data");
var registry = new Dictionary<ProviderBinding, IBatchExecution> { [execution] = worker };
var newDefault = execution with { Provider = "Other.Recording", Version = "2.0.0" };
registry[newDefault] = new RecordingExecution(newDefault);
Check(ReferenceEquals(registry[work.Execution], worker), "changed-default-preserves-original-run-binding");
Check(!registry.ContainsKey(execution with { Version = "missing" }), "missing-old-provider-requires-repair-no-fallback");
try
{
    new Coordinator(NewAttempt("wrong-provider"), snapshot).Dispatch(registry[newDefault], now);
    Check(false, "wrong-provider");
}
catch (InvalidOperationException)
{
    Check(true, "incompatible-execution-binding-rejected");
}
Console.WriteLine("WORKFLOW_CONFORMANCE_ONLY: no durable-store, Docker, Azure, Kubernetes or platform qualification");

sealed class Coordinator(Attempt attempt, InputSnapshot input)
{
    // Model of atomically admitted work + outbox intent. A real store must prove atomic durability.
    public bool PendingDispatch { get; private set; } = true;
    public Submission Submission { get; private set; } = Submission.Unknown;
    public bool CleanupPending { get; private set; } = true;
    public void Dispatch(IBatchExecution provider, DateTimeOffset now)
    {
        if (provider.Binding != attempt.Execution) throw new InvalidOperationException("Wrong bound provider");
        if (now >= attempt.Deadline || !PendingDispatch) return;
        Submission = provider.Submit(attempt, input);
        PendingDispatch = Submission != Submission.Accepted;
    }
    public bool Cleanup(IBatchExecution execution, IBatchExchange exchange)
    {
        if (execution.Binding != attempt.Execution || exchange.Binding != attempt.Exchange)
            throw new InvalidOperationException("Cleanup must use original bindings");
        if (!execution.Cleanup(attempt) || !exchange.Erase(attempt)) return false;
        CleanupPending = false; return true;
    }
}

sealed class Authorization
{
    private readonly Dictionary<string, Attempt> current = [];
    private readonly HashSet<string> closed = [];
    public void Admit(Attempt attempt) { current[attempt.WorkId] = attempt; }
    public void Cancel(Attempt attempt) { if (current.GetValueOrDefault(attempt.WorkId) == attempt) closed.Add(attempt.WorkId); }
    public void Delete(string work) { closed.Add(work); }
    public bool Allows(Attempt attempt, DateTimeOffset now) =>
        current.GetValueOrDefault(attempt.WorkId) == attempt && !closed.Contains(attempt.WorkId) && now < attempt.Deadline;
}

sealed class RecordingExecution(ProviderBinding binding) : IBatchExecution
{
    // Platform identities and state are provider-private. This recording state is volatile.
    private sealed record Handle(string NativeId, ExecutionState State);
    private readonly Dictionary<Attempt, Handle> handles = [];
    public ProviderBinding Binding => binding;
    public bool LoseAcknowledgement { get; set; }
    public bool Unavailable { get; set; }
    public int StartCount { get; private set; }
    public Submission Submit(Attempt attempt, InputSnapshot input)
    {
        if (attempt.Execution != binding) throw new InvalidOperationException("Wrong execution binding");
        if (Unavailable) return Submission.Unknown;
        if (!handles.ContainsKey(attempt))
        {
            handles[attempt] = new("recording-private-" + ++StartCount, ExecutionState.Running);
            if (LoseAcknowledgement) { LoseAcknowledgement = false; return Submission.Unknown; }
        }
        return Submission.Accepted;
    }
    public ExecutionState Observe(Attempt attempt) => Unavailable ? ExecutionState.Unknown :
        handles.GetValueOrDefault(attempt)?.State ?? ExecutionState.Unknown;
    public void RequestStop(Attempt attempt) { /* Sent is not observed stop. */ }
    public void ConfirmStopped(Attempt attempt) { handles[attempt] = handles[attempt] with { State = ExecutionState.Stopped }; }
    public bool Cleanup(Attempt attempt)
    {
        if (Unavailable) return false;
        if (!handles.TryGetValue(attempt, out var handle)) return true;
        if (handle.State != ExecutionState.Stopped) return false;
        handles.Remove(attempt); return true;
    }
}

sealed class RecordingExchange(ProviderBinding binding, Authorization authority) : IBatchExchange
{
    private sealed record InputSlot(InputSnapshot Snapshot, string Content);
    private readonly Dictionary<Attempt, InputSlot> inputs = [];
    private readonly Dictionary<Attempt, ProcessingResult> results = [];
    public ProviderBinding Binding => binding;
    public int PublishCount { get; private set; }
    public InputSnapshot Capture(Attempt attempt, string content, DateTimeOffset now)
    {
        if (attempt.Exchange != binding || !authority.Allows(attempt, now)) throw new InvalidOperationException("Input denied");
        var digest = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(content)));
        var snapshot = new InputSnapshot(attempt.WorkId + "/" + attempt.Generation, digest);
        if (inputs.TryGetValue(attempt, out var prior) && prior.Snapshot != snapshot)
            throw new InvalidOperationException("Input snapshot is immutable");
        inputs[attempt] = new(snapshot, content); return snapshot;
    }
    public string Read(Attempt attempt, InputSnapshot snapshot, DateTimeOffset now)
    {
        if (attempt.Exchange != binding || !authority.Allows(attempt, now) ||
            !inputs.TryGetValue(attempt, out var slot) || slot.Snapshot != snapshot)
            throw new InvalidOperationException("Input read denied");
        return slot.Content;
    }
    public bool Publish(Attempt attempt, ProcessingResult result, DateTimeOffset now)
    {
        // Fencing occurs at this modeled effect owner, not only in the coordinator.
        if (attempt.Exchange != binding || !authority.Allows(attempt, now)) return false;
        if (results.TryGetValue(attempt, out var prior)) return prior == result;
        results[attempt] = result; PublishCount++; return true;
    }
    public bool Erase(Attempt attempt) { inputs.Remove(attempt); results.Remove(attempt); return true; }
}
