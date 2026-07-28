namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// Deterministically migrates Architecture Design 2.0 to its alpha revision.
/// </summary>
public static class ArchitectureDesignV2ToAlpha2Migration
{
    /// <summary>
    /// Preserves every v2 field while replacing only the caller-supplied exact
    /// static-conformance disposition reference.
    /// </summary>
    public static ArchitectureDesignDocumentAlpha2 Migrate(
        ArchitectureDesignDocumentV2 source,
        ArtifactReference suppliedAlphaDisposition)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedAlphaDisposition);
        return new ArchitectureDesignDocumentAlpha2(
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
            suppliedAlphaDisposition);
    }

    internal static ArchitectureDesignDocumentV2 ToLegacyShape(
        ArchitectureDesignDocumentAlpha2 source) =>
        new(
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
            source.StaticConformanceDisposition);
}
