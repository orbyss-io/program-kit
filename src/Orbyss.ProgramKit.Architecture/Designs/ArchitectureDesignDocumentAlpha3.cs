using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Current Architecture Design alpha writer with an exact schema identity.</summary>
public sealed record ArchitectureDesignDocumentAlpha3(
    [property: JsonPropertyName("$schema")] string Schema,
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
    ArtifactReference StaticConformanceDisposition)
{
    /// <summary>The only schema URI emitted by this writer.</summary>
    public const string SchemaUri =
        "https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.3/architecture-design.schema.json";
}
