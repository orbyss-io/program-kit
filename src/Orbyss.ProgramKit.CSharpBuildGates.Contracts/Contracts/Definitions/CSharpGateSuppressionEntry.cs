using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>An exact, source-local, human-authorized suppression.</summary>
public sealed record CSharpGateSuppressionEntry(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier DiagnosticSemanticOwnerId,
    string DiagnosticId,
    ProgramKitIdentifier RuleId,
    SemanticVersion RuleRevision,
    ProgramKitIdentifier ProjectProfileId,
    string RepositoryRelativeSourcePath,
    CSharpGateSuppressionTargetKind TargetKind,
    string Target,
    CSharpGateSuppressionMechanism Mechanism,
    ArtifactReference HumanAuthority,
    string Rationale,
    DateTimeOffset ApprovedAt,
    DateTimeOffset? ExpiresAt,
    string? ReviewCondition,
    Sha256Digest SourceDigest,
    Sha256Digest RuleCatalogDigest,
    Sha256Digest ConfigurationDigest,
    string MigrationOrSupersessionCondition);
