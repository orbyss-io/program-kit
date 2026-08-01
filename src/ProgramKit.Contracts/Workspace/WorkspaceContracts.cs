using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
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

public enum SnapshotFreshness
{
    Current,
    Stale,
    Drifted,
    Unsupported,
    Unavailable,
    Incomplete,
}

public sealed record CandidatePrecondition(
    string LogicalPath,
    ArtifactOwnership Ownership,
    string ExpectedState,
    string? ExpectedDigest);

public sealed record ArtifactManifestEntry(
    string LogicalPath,
    ArtifactOwnership Ownership,
    string MediaType,
    string Digest,
    string ProducerIdentity,
    ClaimClass ClaimClass,
    IReadOnlyList<TraceReference>? Sources = null);

public sealed record CandidateArtifactSet(
    string ConstructionIdentity,
    string CandidateRoot,
    IReadOnlyList<ArtifactManifestEntry> Artifacts,
    string SetDigest,
    CandidateState State,
    ArtifactReference? RootBundle = null,
    IReadOnlyList<CandidatePrecondition>? Preconditions = null,
    IReadOnlyList<GateResult>? GateResults = null);

public sealed record PublicationOperation(
    string Kind,
    string LogicalPath,
    string? ExpectedDigest,
    string NewDigest);

public sealed record PublicationJournal(
    string ConstructionIdentity,
    string ExpectedLiveState,
    IReadOnlyList<PublicationOperation> Operations,
    IReadOnlyList<string> CompletedOperations,
    string State);

public sealed record ArtifactState(
    ArtifactReference Artifact,
    string State,
    string? ObservedDigest,
    IReadOnlyList<EvidenceReference> Evidence);

public sealed record ArtifactClaim(
    ArtifactReference Artifact,
    ClaimClass ClaimClass,
    IReadOnlyList<TraceReference> Sources);

public sealed record AdmissionPublicationReceipt(
    string Schema,
    string ConstructionIdentity,
    string LockDigest,
    string ArtifactSetDigest,
    IReadOnlyList<GateResult> GateResults,
    CandidateState PublicationState,
    string ObservedLiveState,
    IReadOnlyList<ArtifactClaim> Claims,
    IReadOnlyList<EvidenceReference> Support);

public sealed record WorkspaceSnapshot(
    string Schema,
    ArtifactReference RootBundle,
    string ClosureDigest,
    string EvidenceDigest,
    string ConstructionIdentity,
    SnapshotFreshness Freshness,
    IReadOnlyList<GovernedIdentity> Identities,
    IReadOnlyList<JsonObject> SemanticCoverage,
    IReadOnlyList<JsonObject> Bindings,
    IReadOnlyList<ExactSelection> Selections,
    IReadOnlyList<JsonObject> Relationships,
    IReadOnlyList<JsonObject> Seams,
    IReadOnlyList<ArtifactState> Artifacts,
    IReadOnlyList<ArtifactReference> Provenance,
    IReadOnlyList<GateResult> Gates,
    IReadOnlyList<JsonObject> Reviews,
    IReadOnlyList<PolicyWaiver> Waivers,
    IReadOnlyList<EvidenceReference> Evidence,
    IReadOnlyList<ArtifactReference> Receipts,
    IReadOnlyList<JsonObject> Support,
    IReadOnlyList<JsonObject> Retention,
    JsonObject DiagnosticState,
    IReadOnlyList<TraceReference> Trace);
