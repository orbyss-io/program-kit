namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>One reviewed component manifest and its exact evidence reference.</summary>
/// <param name="ManifestReference">Exact immutable manifest artifact.</param>
/// <param name="Manifest">Typed reviewed manifest content.</param>
public sealed record VersionedManifestInput(
    ArtifactReference ManifestReference,
    VersionedComponentManifest Manifest);
