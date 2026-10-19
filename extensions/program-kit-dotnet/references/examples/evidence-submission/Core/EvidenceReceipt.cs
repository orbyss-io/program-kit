namespace ProgramKit.Examples.Evidence;

/// <summary>An owned, established journal observation, independent of HTTP or EF.</summary>
public sealed record EvidenceReceipt(
    string Id,
    string Title,
    DateOnly Date,
    string Hash,
    bool Accepted
);
