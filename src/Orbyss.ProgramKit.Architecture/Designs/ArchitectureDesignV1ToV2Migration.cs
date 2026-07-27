namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Deterministically migrates readable v1 semantics to v2 only when the caller
/// supplies the exact human-selected static-conformance disposition.
/// </summary>
public static class ArchitectureDesignV1ToV2Migration
{
    /// <summary>Creates a v2 value without modifying or defaulting the v1 source.</summary>
    public static ArchitectureDesignDocumentV2 Migrate(
        ArchitectureDesignDocument source,
        ArtifactReference suppliedStaticConformanceDisposition)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedStaticConformanceDisposition);
        return new ArchitectureDesignDocumentV2(
            source.Title,
            source.Intent,
            source.Scope,
            source.NonGoals,
            source.Assumptions,
            source.UnresolvedDecisions,
            source.SourceTruthAuthorities,
            source.Domains,
            source.Contracts,
            source.SemanticModels,
            source.Operations,
            source.Components,
            source.Projects,
            source.Packages,
            source.ReferenceRules,
            source.Extensions,
            source.Configuration,
            source.FeatureActivations,
            source.ArtifactDecisions,
            source.RepresentationRelationships,
            source.Boundaries,
            source.Scenarios,
            source.StatusClaims,
            suppliedStaticConformanceDisposition);
    }
}
