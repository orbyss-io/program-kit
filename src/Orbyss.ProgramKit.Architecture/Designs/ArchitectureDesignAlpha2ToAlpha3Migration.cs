namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Adds the exact schema identity while preserving every design value.</summary>
public static class ArchitectureDesignAlpha2ToAlpha3Migration
{
    /// <summary>Creates the current writer and selects the supplied alpha.2 disposition.</summary>
    public static ArchitectureDesignDocumentAlpha3 Migrate(
        ArchitectureDesignDocumentAlpha2 source,
        ArtifactReference suppliedAlpha2Disposition)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(suppliedAlpha2Disposition);
        return new ArchitectureDesignDocumentAlpha3(
            ArchitectureDesignDocumentAlpha3.SchemaUri,
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
            suppliedAlpha2Disposition);
    }

    internal static ArchitectureDesignDocumentAlpha2 ToAlpha2Shape(
        ArchitectureDesignDocumentAlpha3 source) =>
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
