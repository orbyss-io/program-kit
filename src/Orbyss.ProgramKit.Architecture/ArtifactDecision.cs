using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>Every artifact kind supported by the baseline decision contract.</summary>
public enum SupportedArtifactKind
{
    /// <summary>Human-authored executable or library source.</summary>
    SourceCode,

    /// <summary>Build-project configuration.</summary>
    ProjectConfiguration,

    /// <summary>Package identity, dependency, or packing configuration.</summary>
    PackageConfiguration,

    /// <summary>A machine-readable structural contract.</summary>
    Schema,

    /// <summary>A durable value governed by a schema.</summary>
    SchemaInstance,

    /// <summary>A runtime or design-time configuration value.</summary>
    Configuration,

    /// <summary>A generated manifest.</summary>
    GeneratedManifest,

    /// <summary>A generated catalog.</summary>
    GeneratedCatalog,

    /// <summary>A generated navigation index.</summary>
    GeneratedIndex,

    /// <summary>A provider-neutral agent instruction.</summary>
    ProviderNeutralAgentInstruction,

    /// <summary>A provider-neutral, human-started agent capability.</summary>
    ProviderNeutralAgentCapability,

    /// <summary>A document intended for human explanation.</summary>
    HumanDocument,

    /// <summary>A supplied human decision record.</summary>
    HumanDecisionRecord,

    /// <summary>A reusable test specification.</summary>
    TestSpecification,

    /// <summary>A bounded test execution profile.</summary>
    TestProfile,

    /// <summary>Exact test input or expected-output data.</summary>
    TestFixture,

    /// <summary>Source code generated from canonical inputs.</summary>
    GeneratedCode,

    /// <summary>A human-readable document generated from canonical inputs.</summary>
    GeneratedDocument,

    /// <summary>Ephemeral state named and bounded by a contract.</summary>
    ContractDefinedEphemeralState,

    /// <summary>An OpenAPI integration document.</summary>
    OpenApiDocument,

    /// <summary>An Open Console integration document.</summary>
    OpenConsoleDocument,

    /// <summary>An Open Worker integration document.</summary>
    OpenWorkerDocument,

    /// <summary>An independently versioned component description.</summary>
    VersionComponent,

    /// <summary>An exact observed and target version selection.</summary>
    VersionSelection,

    /// <summary>A typed version-dependency graph.</summary>
    VersionMap,

    /// <summary>An explicit version migration definition.</summary>
    MigrationDefinition,

    /// <summary>A closed migration-impact assessment.</summary>
    MigrationImpactAssessment,

    /// <summary>An immutable JSON serialization profile.</summary>
    JsonSerializationProfile,

    /// <summary>A typed JSON serialization contribution.</summary>
    JsonSerializationContribution,

    /// <summary>Opaque canonical JSON bytes at an approved untyped boundary.</summary>
    CanonicalJsonValue,

    /// <summary>A stable requested-work definition.</summary>
    TaskDefinition,

    /// <summary>A provider-neutral task schedule descriptor.</summary>
    TaskScheduleDescriptor,

    /// <summary>An exact host composition selection.</summary>
    HostComposition,

    /// <summary>A manifest of a deterministic local application publish.</summary>
    LocalPublishManifest,

    /// <summary>Generated operational health configuration.</summary>
    GeneratedHealthConfiguration
}

/// <summary>One outcome's answered nine-question artifact decision.</summary>
public sealed record ArtifactDecision(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string RequestedOutcome,
    SupportedArtifactKind ArtifactKind,
    ExecutableBehaviorAnswer ExecutableBehavior,
    ValueLifecycleAnswer ValueLifecycle,
    AgentRetrievalAnswer AgentRetrieval,
    AgentProcedureAnswer AgentProcedure,
    HumanCommunicationAnswer HumanCommunication,
    GeneratedNavigationAnswer GeneratedNavigation,
    RepresentationAnswer Representation,
    GovernanceAnswer Governance,
    DataHandlingAnswer DataHandling,
    string Rationale);

/// <summary>Question 1: whether the outcome requires executable behavior.</summary>
public sealed record ExecutableBehaviorAnswer(
    bool IsRequired,
    string Rationale);

/// <summary>Ways a value can require a contract-owned artifact.</summary>
public enum ValueLifecycleUse
{
    /// <summary>The value is validated.</summary>
    Validated,

    /// <summary>The value crosses a contract boundary.</summary>
    Exchanged,

    /// <summary>The value is stored beyond an invocation.</summary>
    Persisted,

    /// <summary>The value participates in equality or ordering.</summary>
    Compared,

    /// <summary>The value contributes to a digest.</summary>
    Digested
}

/// <summary>
/// Question 2: whether values are validated, exchanged, persisted, compared,
/// or digested.
/// </summary>
public sealed record ValueLifecycleAnswer(
    ImmutableArray<ValueLifecycleUse> Uses,
    string Rationale);

/// <summary>Question 3: whether agents need bounded retrieval of the artifact.</summary>
public sealed record AgentRetrievalAnswer(
    bool IsRequired,
    string RetrievalBoundary,
    string Rationale);

/// <summary>Question 4: whether the artifact carries agent judgment or procedure.</summary>
public sealed record AgentProcedureAnswer(
    bool IsRequired,
    string HumanStartBoundary,
    string ProcedureBoundary,
    string Rationale);

/// <summary>Question 5: whether the artifact explains or records a human decision.</summary>
public sealed record HumanCommunicationAnswer(
    bool IsRequired,
    string Audience,
    string DecisionAuthorityBoundary,
    string Rationale);

/// <summary>Question 6: whether generated navigation is required.</summary>
public sealed record GeneratedNavigationAnswer(
    bool IsRequired,
    ImmutableArray<ProgramKitIdentifier> SourceIds,
    string GenerationRule,
    string Rationale);

/// <summary>The representation role selected by question 7.</summary>
public enum ArtifactRepresentationRole
{
    /// <summary>The artifact is the authoritative representation.</summary>
    Canonical,

    /// <summary>The artifact is derived from a separately identified canonical artifact.</summary>
    Projection,

    /// <summary>The artifact exists only within a declared transient boundary.</summary>
    Ephemeral
}

/// <summary>Question 7: canonical versus projected representation.</summary>
public sealed record RepresentationAnswer(
    ArtifactRepresentationRole Role,
    ProgramKitIdentifier? CanonicalArtifactId,
    string ProjectionRule,
    string LossPolicy);

/// <summary>
/// Question 8: identity, owner, schema, provenance, digest, consumers,
/// compatibility, and migration responsibilities.
/// </summary>
public sealed record GovernanceAnswer(
    ProgramKitIdentifier ArtifactIdentity,
    ProgramKitIdentifier OwnerId,
    ArtifactReference? Schema,
    string ProvenancePolicy,
    string DigestPolicy,
    ImmutableArray<ProgramKitIdentifier> ConsumerIds,
    string CompatibilityPolicy,
    string MigrationPolicy);

/// <summary>
/// Question 9: redacted, externalized, or ephemeral data treatment.
/// </summary>
public sealed record DataHandlingAnswer(
    bool ContainsSensitiveData,
    string RedactionPolicy,
    string ExternalizationPolicy,
    bool ContainsEphemeralData,
    string EphemeralDataPolicy);
