namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Explicit complete input to deterministic Version Map construction.</summary>
/// <param name="Manifests">Selected exact component manifests.</param>
/// <param name="Dependencies">Typed declarations for every manifest requirement.</param>
public sealed record VersionMapBuildRequest(
    ImmutableArray<VersionedManifestInput> Manifests,
    ImmutableArray<VersionDependencyDeclaration> Dependencies);
