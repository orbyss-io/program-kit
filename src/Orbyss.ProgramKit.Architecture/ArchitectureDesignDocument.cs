using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>
/// The complete, domain-neutral semantic description of a software architecture.
/// Artifact identity, compatibility, provenance, representation, and integrity
/// are supplied by the enclosing <see cref="ArtifactEnvelope{TDocument}"/>.
/// </summary>
public sealed record ArchitectureDesignDocument(
    string Title,
    string Intent,
    ImmutableArray<string> Scope,
    ImmutableArray<string> NonGoals,
    ImmutableArray<string> Assumptions,
    ImmutableArray<UnresolvedDecision> UnresolvedDecisions,
    ImmutableArray<SourceTruthAuthority> SourceTruthAuthorities,
    ImmutableArray<DomainDefinition> Domains,
    ImmutableArray<ContractDefinition> Contracts,
    ImmutableArray<SemanticModelDefinition> SemanticModels,
    ImmutableArray<OperationDefinition> Operations,
    ImmutableArray<ComponentDefinition> Components,
    ImmutableArray<ProjectDefinition> Projects,
    ImmutableArray<PackageDefinition> Packages,
    ImmutableArray<ReferenceRuleDefinition> ReferenceRules,
    ImmutableArray<ExtensionDefinition> Extensions,
    ImmutableArray<ConfigurationDefinition> Configuration,
    ImmutableArray<FeatureActivationDefinition> FeatureActivations,
    ImmutableArray<ArtifactDecision> ArtifactDecisions,
    ImmutableArray<CanonicalProjectionRelationship> RepresentationRelationships,
    ArchitectureBoundarySet Boundaries,
    ImmutableArray<CallerVisibleScenario> Scenarios,
    ImmutableArray<ArchitectureStatusClaim> StatusClaims);

/// <summary>One decision intentionally left open by a design.</summary>
public sealed record UnresolvedDecision(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string Question,
    string DecisionNeededBy,
    string BlockingEffect);

/// <summary>An exact source that has authority over part of a design.</summary>
public sealed record SourceTruthAuthority(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ArtifactReference Source,
    string SourcePath,
    string Governs);

/// <summary>A domain and its exclusively owned vocabulary.</summary>
public sealed record DomainDefinition(
    ProgramKitIdentifier Identity,
    string Purpose,
    ImmutableArray<VocabularyTermDefinition> Vocabulary);

/// <summary>A term whose meaning is owned by the containing domain.</summary>
public sealed record VocabularyTermDefinition(
    string Term,
    string Meaning,
    ImmutableArray<string> AcceptedAliases);

/// <summary>The role of a public contract.</summary>
public enum ContractKind
{
    /// <summary>A request accepted by a caller-visible operation.</summary>
    Request,

    /// <summary>A successful result produced by an operation.</summary>
    Response,

    /// <summary>A stable failure contract.</summary>
    Failure,

    /// <summary>An event-like fact.</summary>
    Contribution,

    /// <summary>A configuration contract.</summary>
    Configuration,

    /// <summary>A public service interface.</summary>
    Service,

    /// <summary>A persisted or exchanged value contract.</summary>
    Value
}

/// <summary>A versioned public contract owned by one domain.</summary>
public sealed record ContractDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerDomainId,
    ContractKind Kind,
    SemanticVersion Version,
    ArtifactReference Schema,
    string Meaning,
    string CompatibilityPolicy);

/// <summary>A named semantic model that is not itself a public exchange contract.</summary>
public sealed record SemanticModelDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerDomainId,
    string Meaning,
    ImmutableArray<ProgramKitIdentifier> TermContractIds,
    string Invariants);

/// <summary>The architectural role of a component.</summary>
public enum ComponentKind
{
    /// <summary>A dependency-light domain contract and semantic model owner.</summary>
    DomainCore,

    /// <summary>An activatable user-visible capability.</summary>
    Feature,

    /// <summary>A replaceable implementation of an owned contract.</summary>
    Provider,

    /// <summary>A non-activatable, single-owner implementation helper.</summary>
    FocusedHelper,

    /// <summary>An explicit translation boundary between owned sides.</summary>
    Bridge,

    /// <summary>A composition root.</summary>
    Host,

    /// <summary>An authoritative design-time input.</summary>
    DesignTimeSource,

    /// <summary>A generated or queried read-only view.</summary>
    ReadProjection,

    /// <summary>An output evaluated against an owned specification.</summary>
    EvaluatedArtifact
}

/// <summary>A deployable, activatable, or supporting architecture component.</summary>
public sealed record ComponentDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ComponentKind Kind,
    string Purpose,
    ImmutableArray<ProgramKitIdentifier> ProvidesContractIds,
    ImmutableArray<ProgramKitIdentifier> ConsumesContractIds,
    bool IsActivatable,
    string CompatibilityBoundary);

/// <summary>A source project and its explicit architecture ownership.</summary>
public sealed record ProjectDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string ProjectPath,
    ImmutableArray<ProgramKitIdentifier> ComponentIds,
    ImmutableArray<ProgramKitIdentifier> ProjectReferenceIds,
    ProgramKitIdentifier? PackageId);

/// <summary>An independently versioned package boundary.</summary>
public sealed record PackageDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    SemanticVersion Version,
    ImmutableArray<ProgramKitIdentifier> ProjectIds,
    ImmutableArray<ProgramKitIdentifier> PackageDependencyIds,
    ImmutableArray<ProgramKitIdentifier> PublicContractIds,
    string CompatibilityBoundary);

/// <summary>Whether a reference is explicitly permitted or prohibited.</summary>
public enum ReferenceRuleDisposition
{
    /// <summary>The described reference is permitted.</summary>
    Allowed,

    /// <summary>The described reference is prohibited.</summary>
    Forbidden
}

/// <summary>An allowed or forbidden reference relation traced to an owner input.</summary>
public sealed record ReferenceRuleDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ReferenceRuleDisposition Disposition,
    string ReferencingScope,
    string ReferencedScope,
    SourceTrace OwnerInput,
    string Rationale);

/// <summary>An exact artifact and location from which a semantic claim was derived.</summary>
public sealed record SourceTrace(
    ArtifactReference Artifact,
    string Path);

/// <summary>An explicitly owned configuration surface.</summary>
public sealed record ConfigurationDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ArtifactReference Schema,
    string Scope,
    string SecretsPolicy,
    string CompatibilityPolicy);

/// <summary>A stable feature activation identity and its configuration ownership.</summary>
public sealed record FeatureActivationDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier FeatureId,
    ProgramKitIdentifier OwnerId,
    ProgramKitIdentifier? ConfigurationId,
    string SelectionSemantics,
    string FailureSemantics);

/// <summary>A relationship between one canonical artifact and a derived projection.</summary>
public sealed record CanonicalProjectionRelationship(
    ProgramKitIdentifier ProjectionId,
    ProgramKitIdentifier CanonicalId,
    string ProjectionRule,
    string LossPolicy,
    bool IsRegenerable);

/// <summary>
/// The nine mandatory cross-cutting boundary statements of an architecture
/// design. Keeping them named prevents a design from silently omitting one.
/// </summary>
public sealed record ArchitectureBoundarySet(
    BoundaryDefinition Security,
    BoundaryDefinition Authority,
    BoundaryDefinition Secrets,
    BoundaryDefinition Persistence,
    BoundaryDefinition Failure,
    BoundaryDefinition Concurrency,
    BoundaryDefinition Cancellation,
    BoundaryDefinition Observability,
    BoundaryDefinition Compatibility);

/// <summary>An owned boundary, its guarantees, and its explicit exclusions.</summary>
public sealed record BoundaryDefinition(
    ProgramKitIdentifier OwnerId,
    string Policy,
    ImmutableArray<string> Guarantees,
    ImmutableArray<string> Exclusions);

/// <summary>A caller-visible scenario used to inspect the architecture as behavior.</summary>
public sealed record CallerVisibleScenario(
    ProgramKitIdentifier Identity,
    string Actor,
    string Intent,
    ImmutableArray<string> Preconditions,
    ImmutableArray<string> Steps,
    ImmutableArray<string> Outcomes,
    ImmutableArray<string> FailureOutcomes);

/// <summary>A truthful implementation status claim with inspectable evidence.</summary>
public sealed record ArchitectureStatusClaim(
    ProgramKitIdentifier SubjectId,
    ArtifactStatus Status,
    ImmutableArray<ArtifactReference> Evidence,
    string Claim);
