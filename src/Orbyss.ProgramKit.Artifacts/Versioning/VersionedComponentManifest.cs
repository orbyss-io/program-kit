using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Describes one independently versioned and consumed component boundary.</summary>
/// <param name="Identity">The stable component identity.</param>
/// <param name="Kind">The boundary kind.</param>
/// <param name="OwnerId">The owning semantic identity.</param>
/// <param name="Version">The component's independent version.</param>
/// <param name="Digest">The exact component digest.</param>
/// <param name="ProvidedContracts">Exact contracts provided by the component.</param>
/// <param name="RequiredContracts">Range-constrained, exactly resolved requirements.</param>
/// <param name="CompatibilityClaims">Independent compatibility claims.</param>
/// <param name="MigrationReferences">Migration definitions available for this revision.</param>
public sealed record VersionedComponentManifest(
    ProgramKitIdentifier Identity,
    VersionBoundaryKind Kind,
    ProgramKitIdentifier OwnerId,
    SemanticVersion Version,
    Sha256Digest Digest,
    ImmutableArray<ArtifactReference> ProvidedContracts,
    ImmutableArray<VersionRequirement> RequiredContracts,
    ImmutableArray<CompatibilityClaim> CompatibilityClaims,
    ImmutableArray<ArtifactReference> MigrationReferences)
{
    /// <summary>Gets the exact component revision represented by this manifest.</summary>
    public ArtifactReference Revision => new(Identity, Version, Digest);
}
