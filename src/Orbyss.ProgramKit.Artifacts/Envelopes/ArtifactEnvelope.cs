using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Envelopes;

/// <summary>The universal immutable envelope for a durable Program Kit artifact.</summary>
/// <typeparam name="TDocument">The immutable typed document view.</typeparam>
/// <param name="Contract">The governing schema contract.</param>
/// <param name="Artifact">Artifact identity and status.</param>
/// <param name="Compatibility">Compatibility claims and migration references.</param>
/// <param name="Provenance">Exact supplied provenance.</param>
/// <param name="Representation">Exact representation profiles.</param>
/// <param name="Integrity">Canonical-byte integrity metadata.</param>
/// <param name="Document">The typed document.</param>
public sealed record ArtifactEnvelope<TDocument>(
    ArtifactContract Contract,
    ArtifactIdentity Artifact,
    ArtifactCompatibility Compatibility,
    ArtifactProvenance Provenance,
    ArtifactRepresentation Representation,
    ArtifactIntegrity Integrity,
    TDocument Document);
