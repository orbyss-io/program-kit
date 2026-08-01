using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Workspace;

public enum CandidateState
{
    Draft,
    Sealed,
    Evaluated,
    PublicationPrepared,
    Publishing,
    PublishedUnadmitted,
    Admitted,
    Rejected,
    Interrupted,
    RecoveryRequired,
}

public sealed record ArtifactManifestEntry(
    string LogicalPath,
    ArtifactOwnership Ownership,
    string MediaType,
    string Digest,
    string ProducerIdentity,
    ClaimClass ClaimClass);

public sealed record CandidateArtifactSet(
    string ConstructionIdentity,
    string CandidateRoot,
    IReadOnlyList<ArtifactManifestEntry> Artifacts,
    string SetDigest,
    CandidateState State);

public sealed record PublicationOperation(string Kind, string LogicalPath, string? ExpectedDigest, string NewDigest);

public sealed record PublicationJournal(
    string ConstructionIdentity,
    string ExpectedLiveState,
    IReadOnlyList<PublicationOperation> Operations,
    IReadOnlyList<string> CompletedOperations,
    string State);
