using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Architecture Design 2.0. The v1 wire model remains independently readable;
/// v2 adds one required exact static-conformance disposition reference.
/// </summary>
public sealed record ArchitectureDesignDocumentV2(
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
    ImmutableArray<ArchitectureStatusClaim> StatusClaims,
    ArtifactReference StaticConformanceDisposition);
