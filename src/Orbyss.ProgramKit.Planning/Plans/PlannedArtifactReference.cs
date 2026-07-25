using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Identifies a planned output without inventing integrity evidence for bytes
/// that do not yet exist.
/// </summary>
/// <param name="Identity">The stable semantic identity of the output.</param>
/// <param name="Version">The planned or materialized semantic version.</param>
/// <param name="State">Whether exact output bytes already exist.</param>
/// <param name="IntegrityDigest">
/// The exact digest when <paramref name="State"/> is materialized; otherwise null.
/// </param>
public sealed record PlannedArtifactReference(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    PlannedArtifactState State,
    Sha256Digest? IntegrityDigest);
