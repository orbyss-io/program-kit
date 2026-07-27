using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A typed, bounded, human-authorized temporary activation exception.</summary>
public sealed record CSharpGateTemporaryActivationExceptionRecord(
    ProgramKitIdentifier Identity,
    ArtifactReference Gate,
    ProgramKitIdentifier RuleId,
    ProgramKitIdentifier ProjectProfileId,
    ProgramKitIdentifier SourceProfileId,
    CSharpGateCommand Command,
    CSharpGateImplementationBoundary Boundary,
    CSharpGateVerificationProfileKind VerificationProfile,
    CSharpGateTemporaryExceptionConditionKind ConditionKind,
    ImmutableArray<CSharpGateConditionParameter> ConditionParameters,
    ProgramKitIdentifier ConsumerOwnerId,
    ArtifactReference HumanAuthority,
    string Rationale,
    string ResidualRisk,
    ImmutableArray<ArtifactReference> CompensatingVerification,
    ImmutableArray<ArtifactReference> EvidenceRequirements,
    DateTimeOffset ActivatedAt,
    DateTimeOffset? ExpiresAt,
    string? RemovalTrigger,
    int? MaximumUses,
    ProgramKitIdentifier RemovalOwnerId);
