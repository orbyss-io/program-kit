using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Envelopes;

/// <summary>Records the digest of canonical envelope bytes.</summary>
/// <param name="Algorithm">The lowercase digest algorithm name.</param>
/// <param name="Digest">The digest calculated with the digest field omitted.</param>
public sealed record ArtifactIntegrity(
    string Algorithm,
    Sha256Digest Digest);
