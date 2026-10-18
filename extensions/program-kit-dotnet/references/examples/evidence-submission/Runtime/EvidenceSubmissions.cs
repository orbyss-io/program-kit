namespace ProgramKit.Examples.Evidence;

/// <summary>Business admission precedes provider allocation; confirmed packets cannot be edited in place.</summary>
public sealed class EvidenceSubmissions(IEvidenceJournal journal) : IEvidenceSubmissions
{
    /// <summary>Admits and retains one immutable owned preparation.</summary>
    public Task<EvidenceReceipt> PrepareAsync(
        string owner,
        EvidencePacket packet,
        CancellationToken cancellation
    )
    {
        AdmitOwner(owner);
        cancellation.ThrowIfCancellationRequested();
        return journal.PrepareAsync(
            owner,
            packet,
            cancellation
        );
    }

    /// <summary>Accepts the retained owned identity without repeating its established effect.</summary>
    public Task<EvidenceReceipt?> AcceptAsync(
        string owner,
        string identity,
        CancellationToken cancellation
    )
    {
        AdmitOwner(owner);
        var validIdentity = Guid.TryParseExact(
            identity,
            "N",
            out _
        );
        if (!validIdentity)
            throw new ArgumentException("Select the retained preparation identity.");
        cancellation.ThrowIfCancellationRequested();
        return journal.AcceptAsync(
            owner,
            identity,
            cancellation
        );
    }

    /// <summary>Observes the existing owned submission without a new business effect.</summary>
    public Task<EvidenceReceipt?> FindAsync(
        string owner,
        string identity,
        CancellationToken cancellation
    )
    {
        AdmitOwner(owner);
        return journal.FindAsync(
            owner,
            identity,
            cancellation
        );
    }

    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private static void AdmitOwner(string owner)
    {
        if (string.IsNullOrWhiteSpace(owner))
            throw new ArgumentException("An admitted owner is required.");
    }
}
