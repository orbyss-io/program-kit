using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

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
