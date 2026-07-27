using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

/// <summary>Deterministic verification evidence 1.0.0.</summary>
public sealed record CSharpBuildGateVerificationEvidenceDocument(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ArtifactReference SelectionLock,
    CSharpGateVerificationProfileKind VerificationProfile,
    bool Succeeded,
    CSharpGateEvidenceLayer? FailureLayer,
    ImmutableArray<ArtifactReference> ParticipationReceipts,
    ImmutableArray<ArtifactReference> ExceptionUseReceipts,
    ImmutableArray<ProgramKitIdentifier> ConsumedSuppressionIds,
    Sha256Digest DiagnosticsDigest,
    Sha256Digest EvidenceDigest);
