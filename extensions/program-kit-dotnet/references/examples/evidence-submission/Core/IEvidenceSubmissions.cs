namespace ProgramKit.Examples.Evidence;

/// <summary>Owned actor intent, admission and observation; no per-endpoint pass-through abstraction.</summary>
public interface IEvidenceSubmissions
{
    /// <summary>Admits and retains one immutable owned preparation.</summary>
    Task<EvidenceReceipt> PrepareAsync(
        string owner,
        EvidencePacket packet,
        CancellationToken cancellation
    );
    /// <summary>Accepts the retained owned identity without repeating its established effect.</summary>
    Task<EvidenceReceipt?> AcceptAsync(
        string owner,
        string identity,
        CancellationToken cancellation
    );
    /// <summary>Observes the existing owned submission without a new business effect.</summary>
    Task<EvidenceReceipt?> FindAsync(
        string owner,
        string identity,
        CancellationToken cancellation
    );
}
