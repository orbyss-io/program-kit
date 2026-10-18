namespace ProgramKit.Examples.Evidence;

/// <summary>HTTP projection of an established owned observation.</summary>
public sealed record EvidenceResponse(
    string Id,
    string Title,
    string Date,
    string Hash,
    bool Accepted,
    string Desk
);
