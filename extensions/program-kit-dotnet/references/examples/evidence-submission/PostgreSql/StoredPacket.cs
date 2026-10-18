namespace ProgramKit.Examples.Evidence;

/// <summary>Private JSON/cache snapshot, deliberately distinct from the public receipt and Core packet.</summary>
internal sealed record StoredPacket(
    string Title,
    DateOnly Date,
    string Hash,
    byte[] Content
);
