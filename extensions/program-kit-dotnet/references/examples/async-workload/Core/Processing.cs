namespace Synthetic.BatchProcessing.Core;

// Application language only: platform handles and transport credentials stay private.
public sealed record ProviderBinding(string Provider, string Version, string ContractVersion, string Scope);
public sealed record Attempt(string WorkId, int Generation, DateTimeOffset Deadline,
    ProviderBinding Execution, ProviderBinding Exchange);
public sealed record InputSnapshot(string Identity, string Sha256);
public sealed record ProcessingResult(string Identity, string Sha256);
public enum Submission { Accepted, Unknown }
public enum ExecutionState { Unknown, Running, Stopped }

public interface IBatchExecution
{
    ProviderBinding Binding { get; }
    Submission Submit(Attempt attempt, InputSnapshot input);
    ExecutionState Observe(Attempt attempt);
    void RequestStop(Attempt attempt);
    bool Cleanup(Attempt attempt);
}

public interface IBatchExchange
{
    ProviderBinding Binding { get; }
    InputSnapshot Capture(Attempt attempt, string content, DateTimeOffset now);
    string Read(Attempt attempt, InputSnapshot snapshot, DateTimeOffset now);
    bool Publish(Attempt attempt, ProcessingResult result, DateTimeOffset now);
    bool Erase(Attempt attempt);
}
